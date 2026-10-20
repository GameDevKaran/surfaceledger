import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from surfaceledger.fixtures import generate
from surfaceledger.pipeline import InputError, analyze, largest_region, quality_masks, read_image, registration, require_opencv5, safe_path


@pytest.fixture(scope="module")
def boards(tmp_path_factory):
    folder = tmp_path_factory.mktemp("owned-fixtures")
    generate(folder)
    return folder


@pytest.mark.parametrize("board", ["board-1", "board-2"])
def test_known_missing_strip_and_recapture(boards, tmp_path, board):
    gap = analyze(boards / board / "gap.json", tmp_path / "gap")
    assert gap["runtime"]["opencv"].startswith("5.")
    assert gap["execution"] == {"location": "local", "aws_verified": False}
    assert gap["summary"]["registered"] == 2
    assert gap["largest_deficient_region"]["bounds_px"] == [320, 0, 448, 512]
    assert gap["largest_deficient_region"]["cell_count"] == 16
    assert gap["largest_deficient_region"]["target_center_px"][0] in (352, 416)
    truth = json.loads((boards / board / "expected.json").read_text())
    for source in gap["sources"]:
        expected_x, expected_y = truth["source_translations_px"][source["id"]]
        matrix = np.array(source["homography"])
        assert matrix[0, 2] == pytest.approx(expected_x, abs=1.0)
        assert matrix[1, 2] == pytest.approx(expected_y, abs=1.0)
    coverage = cv2.imread(str(tmp_path / "gap" / "coverage.png"), cv2.IMREAD_GRAYSCALE) > 0
    expected = np.ones(coverage.shape, bool)
    expected[:, 320:448] = False
    iou = np.count_nonzero(coverage & expected) / np.count_nonzero(coverage | expected)
    assert iou >= 0.98
    recapture = analyze(boards / board / "recaptured.json", tmp_path / "recaptured")
    assert recapture["summary"]["registered"] == 3
    assert recapture["largest_deficient_region"] is None
    assert recapture["summary"]["decision"] == "controlled_quality_thresholds_met"
    assert recapture["summary"]["quality_coverage_fraction"] > 0.99


def test_export_never_fills_gap_or_uses_reference_pixels(boards, tmp_path):
    report = analyze(boards / "board-1" / "gap.json", tmp_path / "result")
    preview = cv2.imread(str(tmp_path / "result" / "source-preview.png"), cv2.IMREAD_UNCHANGED)
    source_index = cv2.imread(str(tmp_path / "result" / "source-index.png"), cv2.IMREAD_UNCHANGED)
    assert not preview[:, 320:448, 3].any()
    assert not source_index[:, 320:448].any()
    assert np.array_equal(preview[:, :, 3] > 0, source_index > 0)
    for index, source in enumerate(report["sources"], 1):
        image = cv2.imread(str(boards / "board-1" / source["file"]))
        sampled = cv2.warpPerspective(image, np.array(source["homography"]), (768, 512), flags=cv2.INTER_NEAREST)
        selection = source_index == index
        assert np.array_equal(preview[selection, :3], sampled[selection])
        assert len(source["sha256"]) == 64
    saved = json.loads((tmp_path / "result" / "report.json").read_text())
    assert saved["reference"]["role"] == "geometry_only_not_coverage"
    assert saved["evidence_kind"] == "synthetic_fixture"


def test_unregistrable_capture_never_becomes_coverage(boards, tmp_path):
    report = analyze(boards / "board-1" / "invalid.json", tmp_path / "result")
    assert report["summary"]["registered"] == 0
    assert report["summary"]["coverage_fraction"] == 0
    assert report["summary"]["quality_coverage_fraction"] == 0
    assert report["sources"][0]["status"] == "unable_to_register"
    assert report["largest_deficient_region"]["bounds_px"] == [0, 0, 768, 512]


def test_blur_is_not_reported_as_good_detail(boards, tmp_path):
    sharp = cv2.imread(str(boards / "board-1" / "right.png"))
    blurred = cv2.imread(str(boards / "board-1" / "blurred.png"))
    good, _ = quality_masks(sharp)
    weak, _ = quality_masks(blurred)
    assert good.mean() > 0.90
    assert weak.mean() < 0.10
    report = analyze(boards / "board-1" / "weak.json", tmp_path / "result")
    assert report["summary"]["quality_coverage_fraction"] < 0.45
    assert all(cell["status"] != "supported" for cell in report["cells"] if cell["col"] >= 7)


def test_glare_cannot_pass_quality_gate(boards, tmp_path):
    report = analyze(boards / "board-1" / "glare.json", tmp_path / "result")
    glare = next(source for source in report["sources"] if source["id"] == "glare")
    assert glare["status"] == "registered"
    assert glare["source_glare_fraction"] > 0.25
    affected = [cell for cell in report["cells"] if 2 <= cell["row"] <= 5 and 8 <= cell["col"] <= 10]
    assert len(affected) == 12
    assert all(cell["status"] == "weak_detail" for cell in affected)
    assert all(cell["quality_coverage"] == 0 for cell in affected)


def test_bad_geometry_rejected_even_with_many_matching_features(boards, monkeypatch):
    image = cv2.imread(str(boards / "board-1" / "left.png"))
    reference = cv2.imread(str(boards / "board-1" / "reference.png"))
    original = cv2.findHomography

    def broken_homography(source, target, *args):
        _, mask = original(source, target, *args)
        return np.array([[1, 0, 10000], [0, 1, 10000], [0, 0, 1]], dtype=float), mask

    monkeypatch.setattr(cv2, "findHomography", broken_homography)
    matrix, evidence = registration(image, reference)
    assert matrix is None
    assert evidence["status"] == "unable_to_register"
    assert evidence["reason"] == "weak_or_localized_geometry"


def test_projective_view_recovers_authored_corner_geometry(boards, tmp_path):
    report = analyze(boards / "board-2" / "perspective.json", tmp_path / "result")
    assert report["summary"]["registered"] == 1
    truth = json.loads((boards / "board-2" / "expected.json").read_text())
    camera = np.float32(truth["perspective_camera_corners_px"])[:, None, :]
    expected = np.float32(truth["perspective_expected_board_corners_px"])
    projected = cv2.perspectiveTransform(camera, np.array(report["sources"][0]["homography"]))[:, 0, :]
    assert np.max(np.linalg.norm(projected - expected, axis=1)) < 3.0


def test_opencv4_is_an_explicit_error(monkeypatch):
    monkeypatch.setattr(cv2, "__version__", "4.14.0")
    with pytest.raises(RuntimeError, match="OpenCV 5 is required"):
        require_opencv5()


@pytest.mark.parametrize("changes", [
    {"planar_surface_confirmed": False},
    {"width_mm": float("nan")},
    {"cell_px": 0},
    {"evidence_kind": "verified_real"},
    {"captures": [{"id": "one", "file": "../outside.png"}]},
])
def test_invalid_manifest_fails_without_report(boards, tmp_path, changes):
    source = boards / "board-1"
    manifest = json.loads((source / "gap.json").read_text())
    manifest.update(changes)
    test_manifest = source / "invalid-manifest.json"
    test_manifest.write_text(json.dumps(manifest))
    with pytest.raises(InputError):
        analyze(test_manifest, tmp_path / "result")
    assert not (tmp_path / "result" / "report.json").exists()


def test_path_escape_and_output_overwrite_are_blocked(boards, tmp_path):
    with pytest.raises(InputError, match="stay inside"):
        safe_path(boards, "../other.png")
    output = tmp_path / "report"
    output.mkdir()
    (output / "report.json").write_text("preserve existing evidence")
    with pytest.raises(InputError, match="new or empty"):
        analyze(boards / "board-1" / "gap.json", output)
    assert (output / "report.json").read_text() == "preserve existing evidence"


def test_recapture_target_is_in_deficient_component_not_hole():
    ring = np.ones((5, 5), np.uint8)
    ring[1:4, 1:4] = 0
    region = largest_region(ring, 64, 320, 320, 320, 320)
    x, y = region["target_center_px"]
    assert ring[int(y // 64), int(x // 64)] == 1
    assert region["cell_count"] == 16


def test_corrupt_image_rejected_before_output(tmp_path):
    corrupt = tmp_path / "broken.png"
    corrupt.write_bytes(b"not an image")
    with pytest.raises(InputError, match="Unsupported or corrupt"):
        read_image(corrupt)
