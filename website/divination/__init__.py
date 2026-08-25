from pathlib import Path

from .core import DivinationEngine, MethodRegistry, PersonaRegistry, ReadingRequest
from .tarot import TarotMethod
from .personas import GenericMasterPersona, LeopardCatPersona


def build_default_engine(base_dir: str | Path) -> DivinationEngine:
    base = Path(base_dir)
    methods = MethodRegistry()
    methods.register(TarotMethod(base / "public" / "manifest.json"))

    personas = PersonaRegistry()
    personas.register(LeopardCatPersona())
    personas.register(GenericMasterPersona())
    return DivinationEngine(methods, personas)


__all__ = [
    "DivinationEngine",
    "MethodRegistry",
    "PersonaRegistry",
    "ReadingRequest",
    "TarotMethod",
    "LeopardCatPersona",
    "GenericMasterPersona",
    "build_default_engine",
]
