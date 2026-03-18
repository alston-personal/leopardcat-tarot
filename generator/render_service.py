#!/usr/bin/env python3
import json
from copy import deepcopy
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from generate_main_image import generate_main_image
from render_card import ROOT, render_card


HOST = "0.0.0.0"
PORT = 8765


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


class RenderHandler(BaseHTTPRequestHandler):
    server_version = "LeopardCatRenderService/0.1"

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: Path):
        if not file_path.exists() or not file_path.is_file():
            self._send_json({"ok": False, "error": "file_not_found"}, status=404)
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"ok": True, "service": "leopardcat-card-generator", "time": datetime.utcnow().isoformat() + "Z"})
            return

        if parsed.path.startswith("/files/"):
            relative_path = unquote(parsed.path.removeprefix("/files/"))
            target = ROOT / relative_path
            self._send_file(target)
            return

        self._send_json({"ok": False, "error": "not_found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/generate-main-image":
            self._handle_generate_main_image()
            return

        if parsed.path != "/render":
            self._send_json({"ok": False, "error": "not_found"}, status=404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "invalid_json"}, status=400)
            return

        config_path = payload.get("config_path", "generator/cards/card-00-the-fool.json")
        output = payload.get("output")
        config_abs = Path(config_path)
        if not config_abs.is_absolute():
            config_abs = ROOT / config_abs

        if not config_abs.exists():
            self._send_json({"ok": False, "error": "config_not_found", "config_path": str(config_abs)}, status=404)
            return

        output_rel = output
        if not output_rel:
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            output_rel = f"art/renders/{config_abs.stem}-{timestamp}.png"

        try:
            config = deepcopy(json.loads(config_abs.read_text()))
            if payload.get("main_image"):
                config["main_image"] = payload["main_image"]
            output_path = render_card(config, output_rel)
        except Exception as exc:
            self._send_json({"ok": False, "error": "render_failed", "detail": str(exc)}, status=500)
            return

        self._send_json(
            {
                "ok": True,
                "config_path": repo_relative(config_abs),
                "output_path": str(output_path),
                "output_relative_path": repo_relative(output_path),
                "preview_url": f"http://127.0.0.1:{PORT}/files/{repo_relative(output_path)}",
                "title": config.get("title"),
                "number": config.get("number"),
                "size": config.get("size"),
                "main_image": config.get("main_image"),
                "main_image_used": bool(config.get("main_image")),
            }
        )

    def _handle_generate_main_image(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "invalid_json"}, status=400)
            return

        config_path = payload.get("config_path", "generator/cards/card-00-the-fool.json")
        config_abs = Path(config_path)
        if not config_abs.is_absolute():
            config_abs = ROOT / config_abs

        config = {}
        if config_abs.exists():
            config = json.loads(config_abs.read_text())

        generation = config.get("generation", {})
        prompt = payload.get("prompt") or generation.get("image_prompt")
        if not prompt:
            self._send_json({"ok": False, "error": "missing_prompt"}, status=400)
            return

        output_rel = payload.get("output")
        if not output_rel:
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            output_rel = f"art/generated/{config_abs.stem}-main-{timestamp}.png"

        model = payload.get("model") or generation.get("model") or "gemini-2.5-flash"
        aspect_ratio = payload.get("aspect_ratio") or generation.get("aspect_ratio") or "2:3"
        image_size = payload.get("image_size") or generation.get("image_size") or "1K"

        try:
            output_path = generate_main_image(
                prompt,
                output_rel,
                model=model,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            )
        except Exception as exc:
            self._send_json({"ok": False, "error": "generate_failed", "detail": str(exc)})
            return

        self._send_json(
            {
                "ok": True,
                "config_path": repo_relative(config_abs),
                "prompt": prompt,
                "output_path": str(output_path),
                "output_relative_path": repo_relative(output_path),
                "preview_url": f"http://127.0.0.1:{PORT}/files/{repo_relative(output_path)}",
                "model": model,
            }
        )


def main():
    server = ThreadingHTTPServer((HOST, PORT), RenderHandler)
    print(f"render service listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
