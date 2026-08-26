# -*- coding: utf-8 -*-
"""Smoke test: POST /api/chat using raw UTF-8 JSON bytes.

This verifies that Chinese input is sent correctly over the wire and that the
server-side response is valid UTF-8 JSON, independent of Windows console code
page issues. Run it while the FastAPI app is up, e.g.:

    .venv\\Scripts\\python.exe scripts\\smoke_utf8.py http://127.0.0.1:8765
"""

import json
import sys
import urllib.request

import pathlib  # noqa: F401  (kept for clarity of output path)


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
    question = "RAG 是什么？"
    payload = json.dumps(
        {"message": question, "session_id": "utf8-verify"}, ensure_ascii=False
    ).encode("utf-8")

    req = urllib.request.Request(
        base.rstrip("/") + "/api/chat",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read()

    out_path = pathlib.Path("data") / "verify-chat-response.bin"
    out_path.write_bytes(body)

    sys.stdout.buffer.write(b"HTTP STATUS: " + str(resp.status).encode("ascii") + b"\n")
    sys.stdout.buffer.write(b"RAW BYTES LEN: " + str(len(body)).encode("ascii") + b"\n")
    decoded = body.decode("utf-8")
    sys.stdout.buffer.write(b"DECODED JSON:\n" + json.dumps(json.loads(decoded), ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    sys.stdout.buffer.write(b"SAVED TO: " + str(out_path.resolve()).encode("utf-8") + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())