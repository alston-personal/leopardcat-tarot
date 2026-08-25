from __future__ import annotations

import json
import os
import ssl
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from divination import ReadingRequest, build_default_engine
from divination.core import DivinationError

BASE_DIR = Path(__file__).resolve().parent
ENGINE = build_default_engine(BASE_DIR)
PORT = int(os.environ.get("DIVINATION_PORT", "8091"))


def load_api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    env_path = Path("/home/ubuntu/agentmanager/.env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None


def call_master(prompt: str) -> str:
    key = load_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7},
    }
    ctx = ssl.create_default_context()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"]


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, body: dict) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {
                "status": "ok",
                "service": "modular-divination-master",
                "methods": ENGINE.methods.capabilities(),
                "personas": ENGINE.personas.capabilities(),
            })
            return
        if self.path == "/api/v1/capabilities":
            self._json(200, {
                "methods": ENGINE.methods.capabilities(),
                "personas": ENGINE.personas.capabilities(),
                "tarot_spreads": ["single", "three_card", "decision", "auto"],
            })
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/api/v1/readings":
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            request = ReadingRequest(
                method=str(body.get("method") or "tarot"),
                persona=str(body.get("persona") or "leopardcat"),
                question=str(body.get("question") or ""),
                input=body.get("input") or {},
                lang=str(body.get("lang") or "zh-TW"),
                seed=body.get("seed"),
            )
            envelope = ENGINE.prepare(request)
            reading = call_master(envelope.master_prompt)
            result = envelope.to_dict()
            result.pop("master_prompt", None)
            result["reading"] = reading
            self._json(200, result)
        except DivinationError as exc:
            self._json(400, {"error": "invalid_request", "message": str(exc)})
        except Exception as exc:
            self._json(500, {"error": "reading_failed", "message": str(exc)})


def main() -> None:
    server = ThreadingHTTPServer(("", PORT), Handler)
    print(f"Modular Divination Master listening on {PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
