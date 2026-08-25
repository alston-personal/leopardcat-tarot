from __future__ import annotations

import base64
import json
import re
import secrets
from pathlib import Path
from typing import Any

from .core import DivinationError

_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
_ALLOWED = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
_MAX_ASSET = 8 * 1024 * 1024

BUILTIN_THEMES = {
    "leopardcat": {
        "theme_id": "leopardcat", "name": "靈山石虎", "source": "builtin",
        "colors": {"background": "#030504", "surface": "#111714", "accent": "#d4af37", "text": "#f4efe4"},
        "background_image": None, "card_back": None,
    },
    "midnight": {
        "theme_id": "midnight", "name": "午夜星空", "source": "builtin",
        "colors": {"background": "#080b17", "surface": "#12182c", "accent": "#9fa8ff", "text": "#f3f5ff"},
        "background_image": None, "card_back": None,
    },
    "minimal-light": {
        "theme_id": "minimal-light", "name": "極簡晨光", "source": "builtin",
        "colors": {"background": "#f5f1e8", "surface": "#ffffff", "accent": "#6e5138", "text": "#28231e"},
        "background_image": None, "card_back": None,
    },
}


def _clean(v: Any, n: int) -> str:
    return re.sub(r"[<>\x00]", "", str(v or "")).strip()[:n]


def _color(v: Any, fallback: str) -> str:
    s = str(v or "").strip()
    return s if re.fullmatch(r"#[0-9a-fA-F]{6}", s) else fallback


class ThemeRegistry:
    def __init__(self, custom_root: str | Path) -> None:
        self.root = Path(custom_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def get(self, theme_id: str | None) -> dict[str, Any]:
        tid = theme_id or "leopardcat"
        if tid in BUILTIN_THEMES:
            return dict(BUILTIN_THEMES[tid])
        if not _SAFE_ID.fullmatch(tid):
            raise DivinationError("invalid theme id")
        p = self.root / tid / "theme.json"
        if not p.exists():
            raise DivinationError("unknown theme")
        return json.loads(p.read_text(encoding="utf-8"))

    def list_builtin(self) -> list[dict[str, Any]]:
        return [{"theme_id": x["theme_id"], "name": x["name"], "source": "builtin"} for x in BUILTIN_THEMES.values()]

    def asset_path(self, theme_id: str, filename: str) -> Path:
        if not _SAFE_ID.fullmatch(theme_id) or not re.fullmatch(r"(?:background|card-back)\.(?:jpg|png|webp)", filename):
            raise DivinationError("invalid theme asset")
        p = self.root / theme_id / "assets" / filename
        if not p.exists():
            raise DivinationError("theme asset not found")
        return p


class ThemePublisher:
    def __init__(self, custom_root: str | Path) -> None:
        self.root = Path(custom_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _save_asset(self, raw_value: Any, asset_dir: Path, stem: str, theme_id: str) -> str | None:
        value = str(raw_value or "")
        if not value:
            return None
        m = re.fullmatch(r"data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=\s]+)", value)
        if not m:
            raise DivinationError("主題圖片格式不支援")
        mime, enc = m.groups()
        raw = base64.b64decode(enc, validate=False)
        if not raw or len(raw) > _MAX_ASSET:
            raise DivinationError("主題圖片單張請小於 8MB")
        ext = _ALLOWED[mime]
        fn = stem + ext
        (asset_dir / fn).write_bytes(raw)
        return f"/api/v1/themes/{theme_id}/assets/{fn}"

    def publish(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = _clean(payload.get("name"), 100) or "我的主題"
        theme_id = f"theme-{secrets.token_hex(4)}"
        td = self.root / theme_id
        assets = td / "assets"
        assets.mkdir(parents=True, exist_ok=False)
        try:
            colors = payload.get("colors") or {}
            background = self._save_asset(payload.get("background_image"), assets, "background", theme_id)
            card_back = self._save_asset(payload.get("card_back"), assets, "card-back", theme_id)
            data = {
                "schema_version": 1, "theme_id": theme_id, "name": name, "source": "custom",
                "colors": {
                    "background": _color(colors.get("background"), "#0b0b10"),
                    "surface": _color(colors.get("surface"), "#171721"),
                    "accent": _color(colors.get("accent"), "#d4af37"),
                    "text": _color(colors.get("text"), "#f5f2ea"),
                },
                "background_image": background, "card_back": card_back,
            }
            (td / "theme.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return data
        except Exception:
            import shutil
            shutil.rmtree(td, ignore_errors=True)
            raise
