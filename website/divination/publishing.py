from __future__ import annotations

import base64
import json
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any

from .core import DivinationError
from .ownership import OwnershipTokens

_ALLOWED_MIME = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
_MAX_IMAGE_BYTES = 8 * 1024 * 1024
_MAX_CARDS = 120


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:42]
    return value or "my-deck"


def _clean_text(value: Any, max_len: int) -> str:
    text = str(value or "").replace("\x00", " ")
    text = re.sub(r"[<>]", "", text)
    text = re.sub(r"[\t\r]+", " ", text)
    return text.strip()[:max_len]


_SHARE_THEME_FIELDS = {
    "layout": 32, "title": 120, "site_tag": 120,
    "background": 80, "surface": 80, "accent": 80,
    "text": 80, "muted": 80, "line": 80,
}


def _clean_share_theme(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    cleaned: dict[str, str] = {}
    for key, max_len in _SHARE_THEME_FIELDS.items():
        if key in value:
            item = _clean_text(value.get(key), max_len)
            if item:
                cleaned[key] = item
    return cleaned


class DeckPublisher:
    def __init__(self, custom_root: str | Path) -> None:
        self.root = Path(custom_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.publish_log = self.root / ".publish-log.json"
        self.hourly_limit = int(os.environ.get("DECK_PUBLISH_LIMIT_PER_HOUR", "20"))
        self.max_decks = int(os.environ.get("DECK_MAX_PUBLISHED", "5000"))
        self.ownership = OwnershipTokens()

    def _check_capacity(self) -> None:
        deck_count = sum(1 for p in self.root.iterdir() if p.is_dir() and (p / "deck.json").exists())
        if deck_count >= self.max_decks:
            raise DivinationError("目前牌組空間已滿，請稍後再試")
        now = int(time.time())
        recent: list[int] = []
        try:
            recent = [int(x) for x in json.loads(self.publish_log.read_text(encoding="utf-8"))]
        except Exception:
            recent = []
        recent = [x for x in recent if now - x < 3600]
        if len(recent) >= self.hourly_limit:
            raise DivinationError("目前建立牌組的人較多，請稍後再試")

    def _record_publish(self) -> None:
        now = int(time.time())
        try:
            recent = [int(x) for x in json.loads(self.publish_log.read_text(encoding="utf-8"))]
        except Exception:
            recent = []
        recent = [x for x in recent if now - x < 3600]
        recent.append(now)
        self.publish_log.write_text(json.dumps(recent[-self.hourly_limit:]), encoding="utf-8")

    def _deck_dir(self, deck_id: str) -> Path:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", deck_id):
            raise DivinationError("invalid deck id")
        path = self.root / deck_id
        if not (path / "deck.json").is_file():
            raise DivinationError("deck not found")
        return path

    def slug_available(self, requested: str) -> dict[str, Any]:
        slug = _clean_text(requested, 64).lower()
        valid = bool(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{1,46}[a-z0-9])?", slug)) and 3 <= len(slug) <= 48
        reserved = {"leopardcat", "admin", "api", "create", "themes", "tarot", "www"}
        available = valid and slug not in reserved and not (self.root / slug).exists()
        return {"slug": slug, "valid": valid, "available": available, "reserved": slug in reserved}

    def publish(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._check_capacity()
        name = _clean_text(payload.get("name"), 100)
        creator = _clean_text(payload.get("creator"), 80)
        description = _clean_text(payload.get("description"), 500)
        cards = payload.get("cards") or []
        reversals = bool(payload.get("reversals", False))
        default_persona = _clean_text(payload.get("persona"), 64).lower() or "master"
        default_theme = _clean_text(payload.get("theme"), 64).lower() or "minimal-light"
        share_theme = _clean_share_theme(payload.get("share_theme"))
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", default_persona):
            raise DivinationError("無效的解牌 Persona")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", default_theme):
            raise DivinationError("無效的牌組主題")
        if not name:
            raise DivinationError("請輸入牌組名稱")
        if not isinstance(cards, list) or not cards:
            raise DivinationError("請至少上傳一張牌")
        if len(cards) > _MAX_CARDS:
            raise DivinationError(f"一次最多 {_MAX_CARDS} 張牌")

        requested_slug = _clean_text(payload.get("slug"), 64).lower()
        if requested_slug:
            check = self.slug_available(requested_slug)
            if not check["valid"]:
                raise DivinationError("專屬網址只能使用 3–48 個英文小寫字母、數字與連字號，且不能以連字號開頭或結尾")
            if check["reserved"]:
                raise DivinationError("這個專屬網址名稱為系統保留字，請換一個")
            if not check["available"]:
                raise DivinationError("這個專屬網址名稱已被使用，請換一個")
            deck_id = requested_slug
        else:
            deck_id = f"{_slug(name)}-{secrets.token_hex(3)}"
        deck_dir = self.root / deck_id
        image_dir = deck_dir / "images"
        try:
            image_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise DivinationError("這個專屬網址名稱剛被其他人使用，請換一個")
        saved_cards: list[dict[str, Any]] = []
        management_token = ""

        try:
            for idx, card in enumerate(cards, start=1):
                title = _clean_text(card.get("title"), 100) or f"Card {idx}"
                upright = _clean_text(card.get("upright"), 2000)
                reversed_meaning = _clean_text(card.get("reversed"), 2000)
                if not upright:
                    raise DivinationError(f"「{title}」還沒有填牌義")
                image = str(card.get("image") or "")
                match = re.fullmatch(r"data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=\s]+)", image)
                if not match:
                    raise DivinationError(f"「{title}」的圖片格式不支援")
                mime, encoded = match.groups()
                raw = base64.b64decode(encoded, validate=False)
                if not raw or len(raw) > _MAX_IMAGE_BYTES:
                    raise DivinationError(f"「{title}」的圖片過大，單張請小於 8MB")
                ext = _ALLOWED_MIME[mime]
                filename = f"card-{idx:03d}{ext}"
                (image_dir / filename).write_bytes(raw)
                saved_cards.append({
                    "id": f"card-{idx:03d}",
                    "title": {"zh": title, "zh-TW": title, "en": title},
                    "meanings": {
                        "upright": upright,
                        "reversed": reversed_meaning if reversals and reversed_meaning else upright,
                    },
                    "image": f"/api/v1/decks/{deck_id}/images/{filename}",
                })

            manifest = {
                "schema_version": 1,
                "deck_id": deck_id,
                "name": name,
                "creator": creator,
                "description": description,
                "reversals": reversals,
                "default_persona": default_persona,
                "default_theme": default_theme,
                "share_theme": share_theme,
                "card_count": len(saved_cards),
                "cards": saved_cards,
            }
            (deck_dir / "deck.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            management_token = self.ownership.issue(deck_dir)
            self._record_publish()
        except Exception:
            import shutil
            shutil.rmtree(deck_dir, ignore_errors=True)
            raise

        return {
            "deck_id": deck_id,
            "name": name,
            "card_count": len(saved_cards),
            "reversals": reversals,
            "default_persona": default_persona,
            "default_theme": default_theme,
            "share_theme": share_theme,
            "share_path": f"/?deck={deck_id}",
            "management_token": management_token,
            "manage_path": f"/manage.html?deck={deck_id}",
        }

    def management_info(self, deck_id: str, token: str) -> dict[str, Any]:
        deck_dir = self._deck_dir(deck_id)
        self.ownership.require(deck_dir, token)
        data = json.loads((deck_dir / "deck.json").read_text(encoding="utf-8"))
        return {
            "resource_type": "deck",
            "deck_id": deck_id,
            "name": data.get("name", deck_id),
            "creator": data.get("creator", ""),
            "description": data.get("description", ""),
            "default_persona": data.get("default_persona", "master"),
            "default_theme": data.get("default_theme", "minimal-light"),
            "share_theme": data.get("share_theme") if isinstance(data.get("share_theme"), dict) else {},
            "reversals": bool(data.get("reversals", False)),
            "card_count": int(data.get("card_count") or len(data.get("cards") or [])),
            "share_path": f"/?deck={deck_id}",
        }

    def update_metadata(self, deck_id: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
        deck_dir = self._deck_dir(deck_id)
        self.ownership.require(deck_dir, token)
        manifest_path = deck_dir / "deck.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))

        if "name" in payload:
            name = _clean_text(payload.get("name"), 100)
            if not name:
                raise DivinationError("牌組名稱不能空白")
            data["name"] = name
        if "creator" in payload:
            data["creator"] = _clean_text(payload.get("creator"), 80)
        if "description" in payload:
            data["description"] = _clean_text(payload.get("description"), 500)
        if "persona" in payload:
            persona = _clean_text(payload.get("persona"), 64).lower()
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", persona):
                raise DivinationError("無效的解牌 Persona")
            data["default_persona"] = persona
        if "theme" in payload:
            theme = _clean_text(payload.get("theme"), 64).lower()
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", theme):
                raise DivinationError("無效的牌組主題")
            data["default_theme"] = theme
        if "share_theme" in payload:
            data["share_theme"] = _clean_share_theme(payload.get("share_theme"))

        manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.management_info(deck_id, token)

    def delete(self, deck_id: str, token: str) -> None:
        deck_dir = self._deck_dir(deck_id)
        self.ownership.require(deck_dir, token)
        import shutil
        shutil.rmtree(deck_dir)

    def rotate_management_token(self, deck_id: str, token: str) -> str:
        return self.ownership.rotate(self._deck_dir(deck_id), token)

    def image_path(self, deck_id: str, filename: str) -> Path:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", deck_id):
            raise DivinationError("invalid deck id")
        if not re.fullmatch(r"card-\d{3}\.(?:jpg|png|webp)", filename):
            raise DivinationError("invalid image path")
        path = self.root / deck_id / "images" / filename
        if not path.exists():
            raise DivinationError("image not found")
        return path