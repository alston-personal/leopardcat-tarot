from pathlib import Path

from .core import DivinationEngine, MethodRegistry, PersonaRegistry, ReadingRequest
from .decks import DeckRegistry
from .tarot import TarotMethod
from .personas import ConfigurablePersona, GenericMasterPersona


def build_default_engine(base_dir: str | Path) -> DivinationEngine:
    base = Path(base_dir)
    decks = DeckRegistry(base / "public" / "manifest.json", base / "data" / "custom_decks")

    methods = MethodRegistry()
    methods.register(TarotMethod(decks))

    personas = PersonaRegistry()
    personas.register(ConfigurablePersona(base / "oracle_packs" / "leopardcat" / "pack.json"))
    personas.register(GenericMasterPersona())
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
    "ConfigurablePersona",
    "GenericMasterPersona",
    "build_default_engine",
]
