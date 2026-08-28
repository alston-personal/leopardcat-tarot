from __future__ import annotations

from arcana_forge.schema import SymbolicUnit
from arcana_forge.systems.base import SymbolicSystem

_MAJOR = [
    (0,"The Fool","beginning, innocence, leap into the unknown",("threshold","forward motion","open sky")),
    (1,"The Magician","will, manifestation, directed skill",("tools","focused gesture","as above so below")),
    (2,"The High Priestess","intuition, mystery, hidden knowledge",("veil","pillars","moon")),
    (3,"The Empress","abundance, nurture, embodied creativity",("fertility","nature","abundance")),
    (4,"The Emperor","structure, authority, stable order",("throne","mountain","structure")),
    (5,"The Hierophant","tradition, teaching, sacred transmission",("teacher","ritual","tradition")),
    (6,"The Lovers","union, choice, alignment of values",("pair","choice","union")),
    (7,"The Chariot","direction, discipline, victorious movement",("vehicle","opposing forces","forward drive")),
    (8,"Strength","courage, compassion, inner mastery",("gentle mastery","animal","infinity")),
    (9,"The Hermit","solitude, searching, inner guidance",("lantern","height","solitude")),
    (10,"Wheel of Fortune","cycles, change, turning conditions",("wheel","cycle","change")),
    (11,"Justice","balance, truth, consequence",("scales","blade","symmetry")),
    (12,"The Hanged Man","suspension, surrender, changed perspective",("inversion","pause","halo")),
    (13,"Death","ending, transformation, irreversible transition",("ending","transition","renewal")),
    (14,"Temperance","integration, moderation, synthesis",("mixing","two vessels","flow")),
    (15,"The Devil","bondage, appetite, shadow attachment",("chains","temptation","shadow")),
    (16,"The Tower","rupture, revelation, collapse of false structure",("tower","lightning","fall")),
    (17,"The Star","hope, renewal, guidance",("star","water","openness")),
    (18,"The Moon","uncertainty, dream, instinct",("moon","path","two guardians")),
    (19,"The Sun","clarity, vitality, joy",("sun","radiance","openness")),
    (20,"Judgement","awakening, reckoning, calling",("summons","rising","recognition")),
    (21,"The World","completion, integration, wholeness",("wreath","four quarters","completion")),
]
_SUITS = {
    "wands": ("fire, action, will", "wand"),
    "cups": ("water, feeling, relationship", "cup"),
    "swords": ("air, thought, conflict, truth", "sword"),
    "pentacles": ("earth, body, work, resources", "pentacle"),
}
_RANKS = ["Ace","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten","Page","Knight","Queen","King"]


class TarotSystem(SymbolicSystem):
    id = "tarot-rws"
    version = "1"

    def units(self) -> tuple[SymbolicUnit, ...]:
        result = [
            SymbolicUnit(f"major-{n:02d}", n, name, archetype, tuple(x.strip() for x in archetype.split(",")), cues, {"arcana":"major"})
            for n,name,archetype,cues in _MAJOR
        ]
        number = 22
        for suit,(meaning,symbol) in _SUITS.items():
            for rank_index,rank in enumerate(_RANKS, 1):
                result.append(SymbolicUnit(
                    f"{suit}-{rank_index:02d}", number, f"{rank} of {suit.title()}",
                    f"{rank.lower()} expression of {meaning}",
                    tuple(x.strip() for x in meaning.split(",")),
                    (symbol, f"quantity/rank cue: {rank}"),
                    {"arcana":"minor","suit":suit,"rank":rank},
                ))
                number += 1
        return tuple(result)
