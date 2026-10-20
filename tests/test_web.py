import base64
import copy
import json
from pathlib import Path
import struct
import threading
from types import SimpleNamespace
from urllib.request import Request, urlopen
import zlib

import pytest

from surfaceledger.web import (
    ApiError, LIMITS, LocalServer, decode_upload, execution_context,
    handle_request, json_bytes, prepare_request, sample,
)
from lambda_handler import handler

ORIGIN = "https://surfaceledger.example"


@pytest.fixture(scope="module")
def gap():
    return json.loads(sample("gap"))["request"]


def call(method, path, headers=None, body=b""):
    return handle_request(method, path, headers or {}, body, origin=ORIGIN, execution=execution_context())


def test_origin_body_method_and_route_guards():
    assert call("POST", "/api/analyze", {"content-type": "application/json"})[0] == 403
    assert call("POST", "/api/analyze", {"origin": "https://evil.invalid", "content-type": "application/json"})[0] == 403
    assert call("POST", "/api/analyze", {"origin": ORIGIN, "content-type": "text/plain"})[0] == 415
    assert call("POST", "/api/analyze", {"origin": ORIGIN, "content-type": "application/json"}, b"x"*(LIMITS["requestBytes"]+1))[0] == 413
    assert call("POST", "/api/analyze", {"origin": ORIGIN, "content-type": "application/json"}, b'{"a":NaN}')[0] == 400
    assert call("DELETE", "/api/analyze")[0] == 405
    assert call("GET", "/../../.env")[0] == 404


def test_upload_header_bomb_rejected_before_decode(gap):
    raw = bytearray(base64.b64decode(gap["reference"]["base64"]))
    raw[16:24] = struct.pack(">II", 90000, 90000)
    raw[29:33] = struct.pack(">I", zlib.crc32(raw[12:29]) & 0xFFFFFFFF)
    with pytest.raises(ApiError, match="dimensions"):
        decode_upload({"name":"bomb.png","base64":base64.b64encode(raw).decode()}, LIMITS["referencePixels"])


def test_untrusted_name_cannot_select_files(gap, tmp_path):
    request = copy.deepcopy(gap)
    request["reference"]["name"] = "../../untrusted.png"
    manifest, names = prepare_request(request, tmp_path)
    saved = json.loads(manifest.read_bytes())
    assert saved["reference"] == "reference.png"
    assert names["reference"] == "../../untrusted.png"
    assert {p.name for p in tmp_path.iterdir()} == {"reference.png","capture-1.png","capture-2.png","capture-set.json"}


def test_inputs_bounded_and_unknown_fields_refused(gap, tmp_path):
    request = copy.deepcopy(gap)
    request["captures"] *= 4
    with pytest.raises(ApiError, match="between 1 and 6"):
        prepare_request(request, tmp_path)
    request = {**gap, "output": "../../outside"}
    with pytest.raises(ApiError, match="unsupported"):
        prepare_request(request, tmp_path)
    with pytest.raises(ApiError, match="base64"):
        decode_upload({"name":"bad.png","base64":"%"}, 1000)


def test_lambda_adapter_is_only_local_contract_evidence(monkeypatch):
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
    monkeypatch.setenv("SURFACELEDGER_PUBLIC_ORIGIN", ORIGIN)
    event = {"requestContext":{"http":{"method":"GET"}}, "rawPath":"/api/health", "headers":{}}
    response = handler(event, SimpleNamespace(aws_request_id="explicit-test-double"))
    data = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert data["runtime"]["opencv"].startswith("5.")
    assert data["execution"]["location"] == "local"
    assert data["execution"]["aws_verified"] is False
    assert data["execution"]["request_id"] is None
    monkeypatch.delenv("SURFACELEDGER_PUBLIC_ORIGIN")
    assert handler(event, SimpleNamespace())[ "statusCode"] == 503


def test_emulator_identifiers_do_not_prove_cloud_execution(monkeypatch):
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "explicit-local-emulator")
    monkeypatch.delenv("SURFACELEDGER_RUNTIME_MODE", raising=False)
    evidence = execution_context("explicit-test-request")
    assert evidence["location"] == "local"
    assert evidence["aws_verified"] is False
    assert evidence["request_id"] is None


def test_real_http_compute_and_source_only_response(gap):
    server = LocalServer(("127.0.0.1", 0))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(server.origin+"/api/health", timeout=5) as response:
            assert json.load(response)["execution"]["location"] == "local"
        request = Request(server.origin+"/api/analyze", data=json_bytes(gap), method="POST",
                          headers={"Origin":server.origin,"Content-Type":"application/json"})
        with urlopen(request, timeout=40) as response:
            data = json.load(response)
            assert response.headers["X-Content-Type-Options"] == "nosniff"
        report = data["report"]
        assert report["runtime"]["opencv"].startswith("5.")
        assert report["execution"]["aws_verified"] is False
        assert report["summary"]["registered"] == 2
        assert report["largest_deficient_region"]["bounds_px"] == [320,0,448,512]
        assert report["sources"][0]["original_name"] == "left.png"
        assert set(data["artifacts"]) == {"preview","coverage","quality","source_index"}
        import hashlib
        for artifact in data["artifacts"].values():
            raw = base64.b64decode(artifact["base64"], validate=True)
            assert raw.startswith(b"\x89PNG")
            assert hashlib.sha256(raw).hexdigest() == artifact["sha256"]
        # No result identifier is retrievable by another browser/request.
        assert call("GET", f"/api/results/{data['runId']}")[0] == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)
