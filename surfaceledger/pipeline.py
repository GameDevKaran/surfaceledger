"""Geometry registration and conservative, source-backed coverage evidence."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import time

# Bound decoder allocation as well as checking decoded dimensions. Set before the
# CLI imports OpenCV; web/worker entrypoints must likewise import this module first.
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = "16000000"
import cv2
import numpy as np

MAX_PIXELS = 16_000_000
MAX_BYTES = 25_000_000
MAX_CAPTURES = 32
POLICY = {
    "version": "controlled-planar-v1",
    "minimum_matches": 16,
    "minimum_inliers": 12,
    "minimum_inlier_ratio": 0.5,
    "maximum_reprojection_rmse_px": 2.5,
    "minimum_inlier_spread": 0.12,
    "minimum_geometry_overlap": 0.25,
    "focus_window_px": 32,
    "minimum_laplacian_variance": 80.0,
    "glare_gray_threshold": 250,
    "maximum_glare_fraction": 0.08,
    "source_boundary_exclusion_px": 1,
    "minimum_cell_coverage": 0.95,
    "minimum_cell_quality_coverage": 0.90,
}


class InputError(ValueError):
    pass


def require_opencv5() -> dict:
    if cv2.__version__.split(".")[0] != "5":
        raise RuntimeError(f"OpenCV 5 is required; found {cv2.__version__}. No version fallback.")
    return {
        "opencv": cv2.__version__,
        "numpy": np.__version__,
        "opencv_build_sha256": hashlib.sha256(cv2.getBuildInformation().encode()).hexdigest(),
    }


def safe_path(base: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise InputError("Image paths must be nonempty paths relative to the capture-set directory.")
    path = (base / name).resolve()
    if not path.is_relative_to(base.resolve()):
        raise InputError("Image paths must stay inside the capture-set directory.")
    return path


def read_image(path: Path) -> tuple[np.ndarray, str]:
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise InputError("Image is missing or exceeds 25 MB.")
    raw = path.read_bytes()
    try:
        image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    except cv2.error as error:
        raise InputError("Image is corrupt, unsupported or exceeds decoder limits.") from error
    if image is None:
        raise InputError("Unsupported or corrupt image.")
    h, w = image.shape[:2]
    if min(h, w) < 96 or h * w > MAX_PIXELS:
        raise InputError("Image must be at least 96 pixels on each side and at most 16 megapixels.")
    return image, hashlib.sha256(raw).hexdigest()


def validate_manifest(manifest: dict) -> None:
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise InputError("Capture set requires schema_version 1.")
    if manifest.get("evidence_kind") not in ("synthetic_fixture", "camera_capture"):
        raise InputError("Declare evidence_kind as synthetic_fixture or camera_capture.")
    if manifest.get("planar_surface_confirmed") is not True:
        raise InputError("Confirm a flat surface; this pipeline cannot certify planarity.")
    for key in ("width_mm", "height_mm"):
        value = manifest.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 1 <= value <= 100_000:
            raise InputError(f"{key} must be a finite physical dimension between 1 and 100000.")
    cell = manifest.get("cell_px", 64)
    if type(cell) is not int or not 16 <= cell <= 256:
        raise InputError("cell_px must be an integer between 16 and 256.")
    captures = manifest.get("captures")
    if not isinstance(captures, list) or not 1 <= len(captures) <= MAX_CAPTURES:
        raise InputError(f"Supply between 1 and {MAX_CAPTURES} captures.")
    names = set()
    for capture in captures:
        if not isinstance(capture, dict) or not isinstance(capture.get("id"), str):
            raise InputError("Every capture requires an id and file.")
        name = capture["id"]
        if not name or len(name) > 80 or name in names:
            raise InputError("Capture ids must be unique, nonempty and at most 80 characters.")
        names.add(name)


def registration(image: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray | None, dict]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ref_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    orb = cv2.ORB_create(nfeatures=5000, fastThreshold=12)
    keys, descriptors = orb.detectAndCompute(gray, None)
    ref_keys, ref_descriptors = orb.detectAndCompute(ref_gray, None)
    evidence = {"status": "unable_to_register", "reason": "insufficient_distinctive_features"}
    if descriptors is None or ref_descriptors is None:
        return None, evidence
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = matcher.knnMatch(descriptors, ref_descriptors, k=2)
    matches = [pair[0] for pair in pairs if len(pair) == 2 and pair[0].distance < 0.72 * pair[1].distance]
    # Repeated textures must not count multiple source features against one reference point.
    unique = {}
    for match in sorted(matches, key=lambda match: match.distance):
        unique.setdefault(match.trainIdx, match)
    matches = list(unique.values())
    evidence["matches"] = len(matches)
    if len(matches) < POLICY["minimum_matches"]:
        return None, evidence
    source = np.float32([keys[match.queryIdx].pt for match in matches])
    target = np.float32([ref_keys[match.trainIdx].pt for match in matches])
    cv2.setRNGSeed(17)
    matrix, mask = cv2.findHomography(source, target, cv2.RANSAC, 3.0)
    if matrix is None or mask is None or not np.isfinite(matrix).all():
        evidence["reason"] = "homography_failed"
        return None, evidence
    inliers = mask.ravel().astype(bool)
    count = int(inliers.sum())
    evidence.update(inliers=count, inlier_ratio=round(count / len(matches), 4))
    if count < POLICY["minimum_inliers"] or count / len(matches) < POLICY["minimum_inlier_ratio"]:
        evidence["reason"] = "insufficient_consensus"
        return None, evidence
    projected = cv2.perspectiveTransform(source[inliers, None, :], matrix)[:, 0, :]
    rmse = float(np.sqrt(np.mean(np.sum((projected - target[inliers]) ** 2, axis=1))))
    h, w = image.shape[:2]
    spread = float(cv2.contourArea(cv2.convexHull(source[inliers]))) / (w * h)
    evidence.update(reprojection_rmse_px=round(rmse, 4), inlier_spread=round(spread, 4))
    if rmse > POLICY["maximum_reprojection_rmse_px"] or spread < POLICY["minimum_inlier_spread"]:
        evidence["reason"] = "weak_or_localized_geometry"
        return None, evidence
    corners = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
    denominators = np.c_[corners, np.ones(4)] @ matrix[2, :]
    if np.any(np.abs(denominators) < 1e-8) or not (np.all(denominators > 0) or np.all(denominators < 0)):
        evidence["reason"] = "projective_horizon"
        return None, evidence
    polygon = cv2.perspectiveTransform(corners[:, None, :], matrix)[:, 0, :]
    area = float(cv2.contourArea(polygon, oriented=True))
    rh, rw = reference.shape[:2]
    if not np.isfinite(polygon).all() or not cv2.isContourConvex(polygon) or area < 256 or area > rw * rh * 16:
        evidence["reason"] = "invalid_projected_boundary"
        return None, evidence
    board = np.float32([[0, 0], [rw - 1, 0], [rw - 1, rh - 1], [0, rh - 1]])
    overlap, _ = cv2.intersectConvexConvex(polygon, board)
    if overlap / area < POLICY["minimum_geometry_overlap"]:
        evidence["reason"] = "outside_calibrated_surface"
        return None, evidence
    evidence.update(
        status="registered",
        reason=None,
        homography=matrix.tolist(),
        projected_boundary_px=polygon.tolist(),
    )
    return matrix, evidence


def quality_masks(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    focused = np.zeros(gray.shape, np.uint8)
    glare = (gray >= POLICY["glare_gray_threshold"]).astype(np.uint8)
    size = POLICY["focus_window_px"]
    for y in range(0, gray.shape[0], size):
        for x in range(0, gray.shape[1], size):
            patch = gray[y:y + size, x:x + size]
            if min(patch.shape) < 8:
                continue
            focus = float(cv2.Laplacian(patch, cv2.CV_64F).var())
            glare_fraction = float(glare[y:y + size, x:x + size].mean())
            if focus >= POLICY["minimum_laplacian_variance"] and glare_fraction <= POLICY["maximum_glare_fraction"]:
                focused[y:y + size, x:x + size] = 1
    # Bright source samples never become qualified evidence.
    focused[glare > 0] = 0
    return focused, glare


def largest_region(deficient: np.ndarray, cell: int, width: int, height: int, width_mm: float, height_mm: float) -> dict | None:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(deficient.astype(np.uint8), connectivity=4)
    if count <= 1:
        return None
    # Actual pixel area matters for partial cells at the board's right/bottom edges.
    regions = []
    for label in range(1, count):
        coordinates = np.argwhere(labels == label)
        area = sum(min(cell, height - int(row) * cell) * min(cell, width - int(col) * cell) for row, col in coordinates)
        regions.append((area, label, coordinates))
    area, label, coordinates = max(regions, key=lambda item: (item[0], -item[1]))
    left, top, cols, rows, _ = stats[label].tolist()
    x0, y0 = left * cell, top * cell
    x1, y1 = min(width, (left + cols) * cell), min(height, (top + rows) * cell)
    # Target an actual deficient cell, rather than a bounding-box center that might be sound.
    centroid = coordinates.mean(axis=0)
    row, col = min(coordinates.tolist(), key=lambda point: sum((np.array(point) - centroid) ** 2))
    target = [min(width, (col + 0.5) * cell), min(height, (row + 0.5) * cell)]
    return {
        "cell_count": len(coordinates),
        "area_px": int(area),
        "cells": [[int(row), int(col)] for row, col in coordinates],
        "bounds_px": [x0, y0, x1, y1],
        "bounds_mm": [round(x0 / width * width_mm, 2), round(y0 / height * height_mm, 2), round(x1 / width * width_mm, 2), round(y1 / height * height_mm, 2)],
        "target_center_px": target,
        "target_center_mm": [round(target[0] / width * width_mm, 2), round(target[1] / height * height_mm, 2)],
        "instruction": "Recapture this deficient region with overlap into already registered detail.",
    }


def analyze(manifest_path: Path, output: Path) -> dict:
    started = time.perf_counter()
    runtime = require_opencv5()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise InputError("Output directory must be new or empty.")
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_file() or manifest_path.stat().st_size > 100_000:
        raise InputError("Capture-set manifest is missing or too large.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    base = manifest_path.parent
    reference, reference_sha = read_image(safe_path(base, manifest.get("reference")))
    h, w = reference.shape[:2]
    cell = manifest.get("cell_px", 64)
    rows, cols = math.ceil(h / cell), math.ceil(w / cell)
    covered = np.zeros((h, w), np.uint8)
    qualified = np.zeros((h, w), np.uint8)
    source_index = np.zeros((h, w), np.uint16)
    # Every nontransparent preview pixel is a nearest-neighbor sample from an input.
    preview = np.zeros((h, w, 4), np.uint8)
    sources = []
    contribution = {}
    for index, capture in enumerate(manifest["captures"], 1):
        path = safe_path(base, capture.get("file"))
        image, sha = read_image(path)
        matrix, evidence = registration(image, reference)
        source = {"id": capture["id"], "file": capture["file"], "sha256": sha, **evidence}
        sources.append(source)
        if matrix is None:
            continue
        source_valid = np.ones(image.shape[:2], np.uint8)
        source_valid[:1, :] = source_valid[-1:, :] = 0
        source_valid[:, :1] = source_valid[:, -1:] = 0
        focus, glare = quality_masks(image)
        projected = cv2.warpPerspective(source_valid, matrix, (w, h), flags=cv2.INTER_NEAREST)
        good = cv2.warpPerspective(focus * source_valid, matrix, (w, h), flags=cv2.INTER_NEAREST)
        source["source_glare_fraction"] = round(float(glare.mean()), 4)
        source["qualified_source_fraction"] = round(float((focus * source_valid).mean()), 4)
        # Prefer qualified evidence; never replace a qualified pixel with a weaker one.
        take = (projected > 0) & ((covered == 0) | ((good > 0) & (qualified == 0)))
        warped = cv2.warpPerspective(image, matrix, (w, h), flags=cv2.INTER_NEAREST)
        preview[take, :3] = warped[take]
        preview[take, 3] = 255
        source_index[take] = index
        covered |= projected
        qualified |= good
        # Keep only cell-level contributions, not two full rasters per capture.
        contribution[capture["id"]] = {
            (row, col): (
                float(projected[row * cell:min(h, (row + 1) * cell), col * cell:min(w, (col + 1) * cell)].mean()),
                float(good[row * cell:min(h, (row + 1) * cell), col * cell:min(w, (col + 1) * cell)].mean()),
            )
            for row in range(rows) for col in range(cols)
        }
    cells = []
    deficient = np.ones((rows, cols), np.uint8)
    for row in range(rows):
        for col in range(cols):
            y0, y1 = row * cell, min(h, (row + 1) * cell)
            x0, x1 = col * cell, min(w, (col + 1) * cell)
            region = np.s_[y0:y1, x0:x1]
            coverage = float(covered[region].mean())
            quality = float(qualified[region].mean())
            status = "missing" if coverage < POLICY["minimum_cell_coverage"] else "weak_detail" if quality < POLICY["minimum_cell_quality_coverage"] else "supported"
            deficient[row, col] = int(status != "supported")
            evidence_sources = [
                {"id": name, "coverage": round(values[(row, col)][0], 4), "quality_coverage": round(values[(row, col)][1], 4)}
                for name, values in contribution.items() if values[(row, col)][0] > 0
            ]
            cells.append({"row": row, "col": col, "bounds_px": [x0, y0, x1, y1], "status": status, "coverage": round(coverage, 4), "quality_coverage": round(quality, 4), "sources": evidence_sources})
    next_region = largest_region(deficient, cell, w, h, manifest["width_mm"], manifest["height_mm"])
    report = {
        "schema_version": 1,
        "application": "SurfaceLedger",
        "runtime": runtime,
        "execution": {"location": "local", "aws_verified": False},
        "evidence_kind": manifest["evidence_kind"],
        "policy": dict(POLICY),
        "reference": {"file": manifest["reference"], "sha256": reference_sha, "width_px": w, "height_px": h, "width_mm": manifest["width_mm"], "height_mm": manifest["height_mm"], "role": "geometry_only_not_coverage"},
        "sources": sources,
        "summary": {
            "registered": sum(source["status"] == "registered" for source in sources),
            "rejected": sum(source["status"] != "registered" for source in sources),
            "coverage_fraction": round(float(covered.mean()), 4),
            "quality_coverage_fraction": round(float(qualified.mean()), 4),
            "supported_cells": int((deficient == 0).sum()),
            "total_cells": rows * cols,
            "decision": "recapture_required" if next_region else "controlled_quality_thresholds_met",
        },
        "largest_deficient_region": next_region,
        "cells": cells,
        "artifacts": {"preview": "source-preview.png", "coverage": "coverage.png", "quality": "quality.png", "source_index": "source-index.png"},
        "limitations": [
            "Synthetic fixtures are not camera validation or measured archival quality.",
            "The operator must confirm a planar surface and rectify the reference to the physical board boundary.",
            "Focus thresholds are controlled-scene heuristics; smooth artwork can be classified as weak detail.",
            "Registration can fail or be ambiguous on repeated texture; no nonplanarity guarantee is made.",
            "No restoration or filling is performed. Transparent preview pixels have no source support.",
        ],
        "processing_seconds": round(time.perf_counter() - started, 4),
    }
    # Never overwrite inputs or a previous report, which might be evidence from another run.
    output.mkdir(parents=True, exist_ok=True)
    for filename, pixels in [
        ("source-preview.png", preview), ("coverage.png", covered * 255),
        ("quality.png", qualified * 255), ("source-index.png", source_index),
    ]:
        if not cv2.imwrite(str(output / filename), pixels):
            raise InputError(f"Could not save {filename}.")
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report
