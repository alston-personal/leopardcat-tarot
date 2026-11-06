from pathlib import Path

from .core import DivinationEngine, MethodRegistry, PersonaRegistry, ReadingRequest
from .decks import DeckRegistry
from .tarot import TarotMethod
from .lenormand import LenormandMethod
from .personas import ConfigurablePersona, GenericMasterPersona


def build_default_engine(base_dir: str | Path) -> DivinationEngine:
    base = Path(base_dir)
    decks = DeckRegistry(base / "public" / "manifest.json", base / "data" / "custom_decks")

    methods = MethodRegistry()
    methods.register(TarotMethod(decks))
    methods.register(LenormandMethod())

    personas = PersonaRegistry()
    oracle_pack_root = base / "oracle_packs"
    if oracle_pack_root.exists():
        for pack_path in sorted(oracle_pack_root.glob("*/pack.json")):
            try:
                personas.register(ConfigurablePersona(pack_path))
            except Exception:
                continue
    personas.register(GenericMasterPersona())

    custom_persona_root = base / "data" / "custom_personas"
    if custom_persona_root.exists():
        for pack_path in sorted(custom_persona_root.glob("*/pack.json")):
            try:
                personas.register(ConfigurablePersona(pack_path))
            except Exception:
                # One malformed user pack must not prevent the service from starting.
                continue

    engine = DivinationEngine(methods, personas)
    engine.decks = decks
    return engine


__all__ = [
    "DivinationEngine",
    "MethodRegistry",
    "PersonaRegistry",
    "ReadingRequest",
    "DeckRegistry",
    "TarotMethod",
    "LenormandMethod",
    "ConfigurablePersona",
    "GenericMasterPersona",
    "build_default_engine",
]
