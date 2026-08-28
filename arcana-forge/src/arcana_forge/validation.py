from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .generation import GeneratedAsset
from .schema import SymbolicCollection


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    unit_id: str | None = None


def validate_collection(collection: SymbolicCollection) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    seen: set[str] = set()
    if not collection.units:
        issues.append(ValidationIssue("empty_collection", "collection has no symbolic units"))
    for compiled in collection.units:
        unit = compiled.unit
        if unit.id in seen:
            issues.append(ValidationIssue("duplicate_unit_id", f"duplicate unit id: {unit.id}", unit.id))
        seen.add(unit.id)
        if not unit.name.strip():
            issues.append(ValidationIssue("missing_name", "symbolic unit has no name", unit.id))
        if not unit.archetype.strip():
            issues.append(ValidationIssue("missing_archetype", "symbolic unit has no archetype", unit.id))
        if not compiled.invariants:
            issues.append(ValidationIssue("missing_invariants", "compiled unit has no preserved invariants", unit.id))
        if unit.name not in compiled.prompt:
            issues.append(ValidationIssue("identity_not_in_prompt", "symbolic identity is absent from generation prompt", unit.id))
    return tuple(issues)


def validate_assets(collection: SymbolicCollection, assets: tuple[GeneratedAsset, ...]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    expected = {item.unit.id for item in collection.units}
    actual = {asset.unit_id for asset in assets}
    for missing in sorted(expected - actual):
        issues.append(ValidationIssue("missing_asset", f"missing generated asset for {missing}", missing))
    for extra in sorted(actual - expected):
        issues.append(ValidationIssue("unexpected_asset", f"unexpected generated asset for {extra}", extra))
    for asset in assets:
        path = Path(asset.uri)
        if not path.exists():
            issues.append(ValidationIssue("asset_not_found", f"generated asset path does not exist: {asset.uri}", asset.unit_id))
    return tuple(issues)


def require_valid_collection(collection: SymbolicCollection) -> SymbolicCollection:
    issues = validate_collection(collection)
    if issues:
        joined = "; ".join(f"{issue.code}:{issue.unit_id or '-'}:{issue.message}" for issue in issues)
        raise ValueError(f"ArcanaForge collection validation failed: {joined}")
    return collection


def require_valid_assets(collection: SymbolicCollection, assets: tuple[GeneratedAsset, ...]) -> tuple[GeneratedAsset, ...]:
    issues = validate_assets(collection, assets)
    if issues:
        joined = "; ".join(f"{issue.code}:{issue.unit_id or '-'}:{issue.message}" for issue in issues)
        raise ValueError(f"ArcanaForge asset validation failed: {joined}")
    return assets
