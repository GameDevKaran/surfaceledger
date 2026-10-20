"""Stateless HTTP/Lambda boundary for bounded, user-owned capture sets."""
from __future__ import annotations

import argparse
import base64
import binascii
from functools import lru_cache
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import multiprocessing
import os
from pathlib import Path
import secrets
import struct
import tempfile
import threading
import time
from urllib.parse import parse_qs, urlsplit
import zlib

from .pipeline import InputError, analyze, require_opencv5

LIMITS = {
    "requestBytes": 4_000_000,
    "responseBytes": 5_500_000,
    "totalImageBytes": 2_800_000,
    "imageBytes": 1_500_000,
    "captures": 6,
    "referencePixels": 1_048_576,
    "capturePixels": 2_097_152,
    "totalPixels": 12_000_000,
    "analysisSeconds": 25,
}
WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
WORKER_SLOTS = threading.BoundedSemaphore(1)


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


def json_bytes(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), allow_nan=False).encode("utf-8")


def execution_context(lambda_request_id: str | None = None) -> dict:
    actual_lambda = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME") and lambda_request_id)
    return {
        "location": "aws-lambda" if actual_lambda else "local",
        "aws_verified": actual_lambda,
        "source_commit": os.environ.get("SURFACELEDGER_SOURCE_COMMIT") or None,
        "request_id": lambda_request_id if actual_lambda else None,
        "persistence": "none; request-local files deleted before response",
    }


def image_dimensions(raw: bytes) -> tuple[int, int, str]:
    """Read PNG/JPEG dimensions before allocating a decoded image."""
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        if len(raw) < 33 or raw[8:16] != b"\x00\x00\x00\rIHDR":
            raise ApiError(400, "invalid_image", "PNG requires a valid IHDR header.")
        if zlib.crc32(raw[12:29]) & 0xFFFFFFFF != struct.unpack(">I", raw[29:33])[0]:
            raise ApiError(400, "invalid_image", "PNG header checksum is invalid.")
        width, height = struct.unpack(">II", raw[16:24])
        return width, height, ".png"
    if raw.startswith(b"\xff\xd8"):
        cursor = 2
        dimensions = None
        while cursor < len(raw):
            if raw[cursor] != 0xFF:
                break
            while cursor < len(raw) and raw[cursor] == 0xFF:
                cursor += 1
            if cursor >= len(raw):
                break
            marker = raw[cursor]
            cursor += 1
            if marker in (0xD9, 0xDA):
                break
            if marker == 0x01 or 0xD0 <= marker <= 0xD7:
                continue
            if cursor + 2 > len(raw):
                break
            length = struct.unpack(">H", raw[cursor:cursor + 2])[0]
            if length < 2 or cursor + length > len(raw):
                break
            if marker in (0xC0, 0xC1, 0xC2):
                if length < 8 or dimensions is not None:
                    break
                height, width = struct.unpack(">HH", raw[cursor + 3:cursor + 7])
                dimensions = (width, height, ".jpg")
            elif marker in (0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                raise ApiError(400, "unsupported_image", "Use baseline or progressive JPEG, or PNG.")
            cursor += length
        if dimensions:
            return dimensions
    raise ApiError(400, "unsupported_image", "Only PNG and baseline/progressive JPEG images are accepted.")


def decode_upload(upload: object, pixel_limit: int) -> tuple[bytes, str, str, int]:
    if not isinstance(upload, dict) or set(upload) != {"name", "base64"}:
        raise ApiError(400, "invalid_upload", "Each image requires only name and base64 fields.")
    name = upload["name"]
    encoded = upload["base64"]
    if not isinstance(name, str) or not 1 <= len(name) <= 120 or any(ord(char) < 32 for char in name):
        raise ApiError(400, "invalid_name", "Image names must contain 1–120 printable characters.")
    if not isinstance(encoded, str) or len(encoded) > ((LIMITS["imageBytes"] + 2) // 3) * 4:
        raise ApiError(413, "image_too_large", "An image exceeds the encoded byte limit.")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as error:
        raise ApiError(400, "invalid_base64", "Image data must be valid base64 without a data-URL prefix.") from error
    if not raw or len(raw) > LIMITS["imageBytes"]:
        raise ApiError(413, "image_too_large", "An image exceeds the decoded byte limit.")
    width, height, extension = image_dimensions(raw)
    pixels = width * height
    if min(width, height) < 96 or pixels > pixel_limit:
        raise ApiError(413, "image_dimensions", f"Image dimensions must be at least 96×96 and at most {pixel_limit} pixels.")
    return raw, extension, name, pixels


def prepare_request(payload: object, folder: Path) -> tuple[Path, dict]:
    if not isinstance(payload, dict):
        raise ApiError(400, "invalid_request", "The request must be a JSON object.")
    allowed = {"reference", "captures", "width_mm", "height_mm", "cell_px", "evidence_kind", "planar_surface_confirmed"}
    if set(payload) - allowed:
        raise ApiError(400, "unknown_fields", "The request contains unsupported fields.")
    captures = payload.get("captures")
    if not isinstance(captures, list) or not 1 <= len(captures) <= LIMITS["captures"]:
        raise ApiError(400, "capture_count", "Supply between 1 and 6 captures.")
    if payload.get("cell_px", 64) != 64:
        raise ApiError(400, "cell_size", "This web release uses fixed 64-pixel quality cells.")
    manifest = {key: payload.get(key) for key in ("width_mm", "height_mm", "evidence_kind", "planar_surface_confirmed")}
    manifest.update(schema_version=1, cell_px=64, captures=[])
    from .pipeline import validate_manifest
    # Validate scalar inputs before decoding or running computer vision.
    validate_manifest({**manifest, "captures": [{"id": f"capture-{index}"} for index in range(1, len(captures) + 1)]})
    total_bytes, total_pixels = 0, 0
    names = {}
    for index, upload in enumerate([payload.get("reference"), *captures]):
        raw, extension, display_name, pixels = decode_upload(upload, LIMITS["referencePixels"] if index == 0 else LIMITS["capturePixels"])
        total_bytes += len(raw)
        total_pixels += pixels
        if total_bytes > LIMITS["totalImageBytes"] or total_pixels > LIMITS["totalPixels"]:
            raise ApiError(413, "capture_set_too_large", "The capture set exceeds the total image byte or pixel limit.")
        internal_id = "reference" if index == 0 else f"capture-{index}"
        file = f"{internal_id}{extension}"
        (folder / file).write_bytes(raw)
        names[internal_id] = display_name
        if index == 0:
            manifest["reference"] = file
        else:
            manifest["captures"].append({"id": internal_id, "file": file})
    manifest_path = folder / "capture-set.json"
    manifest_path.write_bytes(json_bytes(manifest))
    return manifest_path, names


def _pipeline_child(manifest: str, output: str, error_path: str) -> None:
    try:
        analyze(Path(manifest), Path(output))
    except InputError as error:
        Path(error_path).write_bytes(json_bytes({"code": "invalid_capture_set", "message": str(error)}))
    except Exception:
        # No input data, user filenames, native stack or credential values in responses.
        Path(error_path).write_bytes(json_bytes({"code": "analysis_failed", "message": "The vision worker could not process this capture set."}))


def run_worker(manifest: Path, output: Path, timeout: float = LIMITS["analysisSeconds"]) -> dict:
    error_path = manifest.parent / "worker-error.json"
    process = multiprocessing.get_context("spawn").Process(
        target=_pipeline_child, args=(str(manifest), str(output), str(error_path)),
    )
    process.start()
    try:
        process.join(timeout)
        if process.is_alive():
            process.terminate()
            process.join(2)
            if process.is_alive():
                process.kill()
                process.join(2)
            raise ApiError(422, "analysis_timeout", "This capture set exceeded the 25-second processing limit. Reduce image sizes or capture count.")
        if error_path.exists():
            error = json.loads(error_path.read_bytes())
            raise ApiError(422, error["code"], error["message"])
        if process.exitcode != 0 or not (output / "report.json").is_file():
            raise ApiError(503, "worker_unavailable", "The vision worker did not finish. Try a smaller capture set.")
        return json.loads((output / "report.json").read_bytes())
    finally:
        if process.is_alive():
            process.terminate()
            process.join(2)
        process.close()


def analyze_upload(payload: object, execution: dict) -> dict:
    if not WORKER_SLOTS.acquire(blocking=False):
        raise ApiError(503, "busy", "The vision worker is processing another capture set. Try again shortly.")
    try:
        # No uploaded images, job results, identifiers or session state survive this context.
        with tempfile.TemporaryDirectory(prefix="surfaceledger-request-") as temporary:
            folder = Path(temporary)
            manifest, names = prepare_request(payload, folder)
            output = folder / "output"
            report = run_worker(manifest, output)
            report["execution"] = dict(execution)
            report["reference"]["original_name"] = names["reference"]
            for source in report["sources"]:
                source["original_name"] = names[source["id"]]
            report["artifacts"]["delivery"] = "inline; browser-owned export"
            artifacts = {}
            for key, filename in (
                ("preview", "source-preview.png"), ("coverage", "coverage.png"),
                ("quality", "quality.png"), ("source_index", "source-index.png"),
            ):
                raw = (output / filename).read_bytes()
                artifacts[key] = {"mime": "image/png", "base64": base64.b64encode(raw).decode("ascii"), "sha256": hashlib.sha256(raw).hexdigest()}
            result = {"runId": secrets.token_hex(16), "report": report, "artifacts": artifacts}
            if len(json_bytes(result)) > LIMITS["responseBytes"]:
                raise ApiError(422, "result_too_large", "The result exceeds the inline export limit. Reduce the reference image size.")
            return result
    finally:
        WORKER_SLOTS.release()


@lru_cache(maxsize=5)
def sample(scenario: str) -> bytes:
    if scenario not in {"gap", "recaptured", "glare", "invalid", "perspective"}:
        raise ApiError(400, "invalid_sample", "Choose gap, recaptured, glare, invalid or perspective.")
    from .fixtures import generate
    with tempfile.TemporaryDirectory(prefix="surfaceledger-owned-sample-") as temporary:
        folder = Path(temporary) / "fixtures"
        generate(folder)
        board = folder / "board-1"
        manifest = json.loads((board / f"{scenario}.json").read_bytes())

        def upload(file: str) -> dict:
            return {"name": file, "base64": base64.b64encode((board / file).read_bytes()).decode("ascii")}

        request = {
            "reference": upload(manifest["reference"]),
            "captures": [upload(capture["file"]) for capture in manifest["captures"]],
            **{key: manifest[key] for key in ("width_mm", "height_mm", "cell_px", "evidence_kind", "planar_surface_confirmed")},
        }
        return json_bytes({
            "label": "Owned synthetic development fixture; not a camera capture",
            "request": request,
            "expected": json.loads((board / "expected.json").read_bytes()),
        })


def handle_request(method: str, path: str, headers: dict, body: bytes, *, origin: str, execution: dict) -> tuple[int, dict, bytes]:
    response_headers = {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Content-Security-Policy": "default-src 'self'; img-src 'self' data: blob:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        "Content-Type": "application/json; charset=utf-8",
    }
    try:
        if not origin or urlsplit(origin).scheme not in ("http", "https") or urlsplit(origin).path not in ("", "/"):
            raise ApiError(503, "origin_configuration", "The application origin is not configured.")
        request_origin = headers.get("origin")
        if request_origin and request_origin != origin.rstrip("/"):
            raise ApiError(403, "origin_rejected", "This request origin is not allowed.")
        url = urlsplit(path)
        if method == "POST":
            if not request_origin:
                raise ApiError(403, "origin_required", "Analysis requests require the application Origin header.")
            if url.path != "/api/analyze":
                raise ApiError(404, "not_found", "No such endpoint.")
            if headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
                raise ApiError(415, "json_required", "Send application/json.")
            if len(body) > LIMITS["requestBytes"]:
                raise ApiError(413, "request_too_large", "The request exceeds 4 MB.")
            try:
                payload = json.loads(body, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
            except (ValueError, UnicodeDecodeError) as error:
                raise ApiError(400, "invalid_json", "Send valid UTF-8 JSON without nonfinite numbers.") from error
            result = analyze_upload(payload, execution)
            return 200, response_headers, json_bytes(result)
        if method != "GET":
            raise ApiError(405, "method_not_allowed", "Use GET or POST.")
        if url.path == "/api/health":
            return 200, response_headers, json_bytes({"application": "SurfaceLedger", "status": "ok", "runtime": require_opencv5(), "execution": execution, "limits": LIMITS})
        if url.path == "/api/sample":
            scenario = parse_qs(url.query).get("scenario", ["gap"])[0]
            return 200, response_headers, sample(scenario)
        static = {"/": ("index.html", "text/html"), "/index.html": ("index.html", "text/html"), "/app.js": ("app.js", "application/javascript"), "/styles.css": ("styles.css", "text/css")}
        if url.path in static:
            filename, mime = static[url.path]
            file = WEB_ROOT / filename
            if not file.is_file():
                raise ApiError(503, "interface_pending", "The web interface is not packaged yet.")
            response_headers["Content-Type"] = mime + "; charset=utf-8"
            return 200, response_headers, file.read_bytes()
        raise ApiError(404, "not_found", "No such endpoint.")
    except ApiError as error:
        return error.status, response_headers, json_bytes({"error": {"code": error.code, "message": error.message}})
    except InputError as error:
        return 400, response_headers, json_bytes({"error": {"code": "invalid_capture_set", "message": str(error)}})
    except (RuntimeError, OSError):
        return 503, response_headers, json_bytes({"error": {"code": "worker_unavailable", "message": "The vision worker is unavailable."}})


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 8

    def __init__(self, address: tuple[str, int], origin: str | None = None):
        super().__init__(address, LocalHandler)
        self.origin = origin or f"http://{address[0]}:{self.server_address[1]}"


class LocalHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self):
        super().setup()
        self.connection.settimeout(35)

    def do_GET(self):
        self.dispatch()

    def do_POST(self):
        self.dispatch()

    def do_OPTIONS(self):
        self.dispatch()

    def dispatch(self):
        headers = {key.lower(): value for key, value in self.headers.items()}
        try:
            if headers.get("transfer-encoding"):
                raise ApiError(400, "unsupported_transfer", "Chunked request bodies are not supported.")
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) > 1:
                raise ApiError(400, "invalid_length", "Supply one Content-Length.")
            length = int(lengths[0]) if lengths else 0
            if length < 0 or length > LIMITS["requestBytes"]:
                raise ApiError(413, "request_too_large", "The request exceeds 4 MB.")
            body = self.rfile.read(length) if length else b""
            if len(body) != length:
                raise ApiError(400, "incomplete_body", "The request body is incomplete.")
            status, response_headers, result = handle_request(self.command, self.path, headers, body, origin=self.server.origin, execution=execution_context())
        except (ApiError, ValueError, TimeoutError) as error:
            code = error.status if isinstance(error, ApiError) else 400
            status, response_headers, result = code, {"Content-Type": "application/json", "Cache-Control": "no-store"}, json_bytes({"error": {"code": error.code if isinstance(error, ApiError) else "invalid_request", "message": error.message if isinstance(error, ApiError) else "Invalid or timed-out request."}})
        self.send_response(status)
        for key, value in response_headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(result)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(result)
        self.close_connection = True

    def log_message(self, *_):
        pass


def main():
    parser = argparse.ArgumentParser(description="Run SurfaceLedger's stateless local web application.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8784)
    args = parser.parse_args()
    server = LocalServer((args.host, args.port), os.environ.get("SURFACELEDGER_PUBLIC_ORIGIN"))
    print(f"SurfaceLedger local: {server.origin}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
