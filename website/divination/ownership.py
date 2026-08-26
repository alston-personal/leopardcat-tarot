from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

from .core import DivinationError


class OwnershipTokens:
    """High-entropy bearer tokens; only SHA-256 hashes are persisted."""

    filename = ".owner.json"

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def issue(self, resource_dir: str | Path) -> str:
        directory = Path(resource_dir)
        directory.mkdir(parents=True, exist_ok=True)
        token = secrets.token_urlsafe(32)
        payload = {
            "schema_version": 1,
            "token_hash": self._hash(token),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        (directory / self.filename).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return token

    def is_managed(self, resource_dir: str | Path) -> bool:
        return (Path(resource_dir) / self.filename).is_file()

    def verify(self, resource_dir: str | Path, token: str) -> bool:
        if not token:
            return False
        try:
            data = json.loads((Path(resource_dir) / self.filename).read_text(encoding="utf-8"))
            expected = str(data.get("token_hash") or "")
        except Exception:
            return False
        return bool(expected) and hmac.compare_digest(expected, self._hash(token))

    def require(self, resource_dir: str | Path, token: str) -> None:
        directory = Path(resource_dir)
        if not self.is_managed(directory):
            raise DivinationError("這是舊版發布內容，尚未建立管理金鑰")
        if not self.verify(directory, token):
            raise DivinationError("管理金鑰不正確")

    def rotate(self, resource_dir: str | Path, token: str) -> str:
        self.require(resource_dir, token)
        return self.issue(resource_dir)
