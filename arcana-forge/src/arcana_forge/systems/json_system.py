from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from arcana_forge.schema import SymbolicUnit
from arcana_forge.systems.base import SymbolicSystem


class JsonSymbolicSystem(SymbolicSystem):
    """Data-driven symbolic-system plugin.

    A custom system defines semantic units only. Divination/random/casting mechanics are intentionally absent.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        system_id = str(data.get("id") or "").strip()
        if not system_id:
            raise ValueError("symbolic system id is required")
        raw_units = data.get("units")
        if not isinstance(raw_units, list) or not raw_units:
            raise ValueError("symbolic system units must be a non-empty list")
        self.id = system_id
        self.version = str(data.get("version") or "1")
        units = []
        seen = set()
        for index, raw in enumerate(raw_units, 1):
            if not isinstance(raw, dict):
                raise ValueError(f"unit {index} must be an object")
            unit_id = str(raw.get("id") or f"unit-{index:03d}").strip()
            if not unit_id or unit_id in seen:
                raise ValueError(f"duplicate/invalid unit id: {unit_id}")
            seen.add(unit_id)
            name = str(raw.get("name") or "").strip()
            archetype = str(raw.get("archetype") or "").strip()
            if not name or not archetype:
                raise ValueError(f"unit {unit_id} requires name and archetype")
            units.append(SymbolicUnit(
                id=unit_id,
                number=int(raw.get("number", index)),
                name=name,
                archetype=archetype,
                keywords=tuple(str(x) for x in raw.get("keywords", []) if str(x).strip()),
                required_cues=tuple(str(x) for x in raw.get("required_cues", []) if str(x).strip()),
                metadata=dict(raw.get("metadata") or {}),
            ))
        self._units = tuple(units)

    @classmethod
    def from_file(cls, path: str | Path) -> "JsonSymbolicSystem":
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("symbolic system file must contain a JSON object")
        return cls(value)

    def units(self) -> tuple[SymbolicUnit, ...]:
        return self._units
