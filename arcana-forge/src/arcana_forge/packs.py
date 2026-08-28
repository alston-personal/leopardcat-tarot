from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .schema import SubjectPack, SubjectSpec, UnitVisualOverride


def subject_pack_from_dict(data: dict[str, Any]) -> SubjectPack:
    pack_id = str(data.get("id") or "").strip()
    if not pack_id:
        raise ValueError("subject pack id is required")
    raw_subject = data.get("subject")
    if not isinstance(raw_subject, dict):
        raise ValueError("subject pack requires subject object")
    concept = str(raw_subject.get("concept") or "").strip()
    if not concept:
        raise ValueError("subject concept is required")
    subject = SubjectSpec(
        concept=concept,
        role=str(raw_subject.get("role") or "recurring visual subject"),
        traits=tuple(str(x) for x in raw_subject.get("traits", []) if str(x).strip()),
    )
    raw_overrides = data.get("unit_overrides") or {}
    if not isinstance(raw_overrides, dict):
        raise ValueError("unit_overrides must be an object")
    overrides = {}
    for unit_id, raw in raw_overrides.items():
        if not isinstance(raw, dict):
            raise ValueError(f"override for {unit_id} must be an object")
        overrides[str(unit_id)] = UnitVisualOverride(
            scene=str(raw.get("scene") or "").strip() or None,
            prompt_addendum=str(raw.get("prompt_addendum") or "").strip() or None,
            meanings={str(k): str(v) for k, v in (raw.get("meanings") or {}).items() if str(v).strip()},
            metadata=dict(raw.get("metadata") or {}),
        )
    return SubjectPack(
        id=pack_id,
        subject=subject,
        unit_overrides=overrides,
        metadata=dict(data.get("metadata") or {}),
    )


def load_subject_pack(path: str | Path) -> SubjectPack:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("subject pack file must contain a JSON object")
    return subject_pack_from_dict(value)


def subject_pack_to_dict(pack: SubjectPack) -> dict[str, Any]:
    return {
        "schema": "arcana-forge.subject-pack/v0.1",
        "id": pack.id,
        "subject": asdict(pack.subject),
        "unit_overrides": {unit_id: asdict(override) for unit_id, override in pack.unit_overrides.items()},
        "metadata": pack.metadata,
    }


def save_subject_pack(pack: SubjectPack, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(subject_pack_to_dict(pack), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target
