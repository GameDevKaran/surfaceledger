"""AWS Lambda Function URL adapter. Cloud execution is not implied by importing it."""
import base64
import binascii
import os

from surfaceledger.web import LIMITS, execution_context, handle_request, json_bytes


def handler(event, context):
    headers = {key.lower(): str(value) for key, value in (event.get("headers") or {}).items()}
    http = (event.get("requestContext") or {}).get("http") or {}
    method = http.get("method", "")
    path = event.get("rawPath", "/")
    query = event.get("rawQueryString", "")
    if query:
        path += "?" + query
    body = event.get("body") or ""
    if not isinstance(body, str) or len(body) > ((LIMITS["requestBytes"] + 2) // 3) * 4:
        return response(413, {"Content-Type": "application/json", "Cache-Control": "no-store"}, json_bytes({"error": {"code": "request_too_large", "message": "The request exceeds 4 MB."}}))
    try:
        raw = base64.b64decode(body, validate=True) if event.get("isBase64Encoded") else body.encode("utf-8")
    except (ValueError, binascii.Error):
        return response(400, {"Content-Type": "application/json", "Cache-Control": "no-store"}, json_bytes({"error": {"code": "invalid_body", "message": "Invalid request body encoding."}}))
    origin = os.environ.get("SURFACELEDGER_PUBLIC_ORIGIN", "")
    execution = execution_context(getattr(context, "aws_request_id", None))
    status, result_headers, result = handle_request(method, path, headers, raw, origin=origin, execution=execution)
    return response(status, result_headers, result)


def response(status, headers, body):
    return {"statusCode": status, "headers": headers, "body": body.decode("utf-8"), "isBase64Encoded": False}
