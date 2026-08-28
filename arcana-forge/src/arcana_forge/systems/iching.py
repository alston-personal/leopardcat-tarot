from __future__ import annotations

from arcana_forge.schema import SymbolicUnit
from arcana_forge.systems.base import SymbolicSystem

_NAMES = [
    "乾","坤","屯","蒙","需","訟","師","比","小畜","履","泰","否","同人","大有","謙","豫",
    "隨","蠱","臨","觀","噬嗑","賁","剝","復","無妄","大畜","頤","大過","坎","離","咸","恆",
    "遯","大壯","晉","明夷","家人","睽","蹇","解","損","益","夬","姤","萃","升","困","井",
    "革","鼎","震","艮","漸","歸妹","豐","旅","巽","兌","渙","節","中孚","小過","既濟","未濟",
]

_THEMES = [
    "creative heaven, initiative, enduring strength", "receptive earth, yielding support, devotion",
    "difficulty at the beginning, sprouting through danger", "youthful folly, learning, disciplined inquiry",
    "waiting, nourishment, confidence before action", "conflict, contention, knowing when to stop",
    "organized collective force, discipline, leadership", "union, alliance, mutual belonging",
    "small restraint, gentle accumulation, preparation", "careful conduct, treading with awareness",
    "peace, exchange between heaven and earth", "stagnation, blocked exchange, withdrawal from corruption",
    "fellowship, shared purpose, community", "great possession, abundance held with clarity",
    "modesty, lowering what is high and raising what is low", "enthusiasm, readiness, inspired movement",
    "following, adaptation, responsive movement", "repairing decay, correcting inherited disorder",
    "approach, growth, benevolent oversight", "contemplation, observation, being seen and seeing",
    "biting through, decisive justice, removing obstruction", "grace, adornment, form supporting substance",
    "splitting apart, erosion, stripping away", "return, renewal, the first movement of yang",
    "innocence, the unexpected, acting without false intent", "great restraint, storing power, disciplined cultivation",
    "nourishment, what enters the mouth and mind", "great excess, structural overload, decisive transition",
    "the abyss, repeated danger, sincerity within risk", "radiance, clarity, attachment to what illuminates",
    "influence, attraction, mutual responsiveness", "duration, constancy, sustainable commitment",
    "retreat, strategic withdrawal, preserving integrity", "great power, strength governed by correctness",
    "progress, advancing into the light", "darkening of the light, protecting clarity under adversity",
    "the family, ordered relationships, roles and trust", "opposition, difference, finding limited common ground",
    "obstruction, difficulty, turning inward for support", "release, untying tension, timely liberation",
    "decrease, reduction that restores balance", "increase, beneficial growth, generous movement",
    "breakthrough, resolute declaration, confronting excess", "coming to meet, sudden encounter, guarding boundaries",
    "gathering together, concentration, shared center", "ascending, gradual growth through receptive effort",
    "oppression, exhaustion, maintaining purpose under constraint", "the well, enduring communal resource",
    "revolution, necessary change when the time is ripe", "the cauldron, transformation, culture and nourishment",
    "thunder, shock, awakening, composure after surprise", "mountain, stillness, stopping at the proper place",
    "gradual development, ordered progress, maturation", "the marrying maiden, subordinate position, imperfect timing",
    "abundance, fullness at the peak, acting before decline", "the traveler, temporary dwelling, clarity without attachment",
    "wind, gentle penetration, repeated influence", "lake, joy, exchange, open communication",
    "dispersion, dissolving separation, restoring connection", "limitation, measured boundaries, sustainable rules",
    "inner truth, sincerity that creates trust", "small excess, attending to small things, modest action",
    "after completion, order achieved yet requiring vigilance", "before completion, transition, careful approach to completion",
]

# Trigram line patterns are bottom -> top. 1 = yang, 0 = yin.
_TRIGRAMS = {
    "heaven": "111", "lake": "110", "fire": "101", "thunder": "100",
    "wind": "011", "water": "010", "mountain": "001", "earth": "000",
}

# King Wen sequence: (upper trigram, lower trigram).
_PAIRS = [
    ("heaven","heaven"),("earth","earth"),("water","thunder"),("mountain","water"),
    ("water","heaven"),("heaven","water"),("earth","water"),("water","earth"),
    ("wind","heaven"),("heaven","lake"),("earth","heaven"),("heaven","earth"),
    ("heaven","fire"),("fire","heaven"),("earth","mountain"),("thunder","earth"),
    ("lake","thunder"),("mountain","wind"),("earth","lake"),("wind","earth"),
    ("fire","thunder"),("mountain","fire"),("mountain","earth"),("earth","thunder"),
    ("heaven","thunder"),("mountain","heaven"),("mountain","thunder"),("lake","wind"),
    ("water","water"),("fire","fire"),("lake","mountain"),("thunder","wind"),
    ("heaven","mountain"),("thunder","heaven"),("fire","earth"),("earth","fire"),
    ("wind","fire"),("fire","lake"),("water","mountain"),("thunder","water"),
    ("mountain","lake"),("wind","thunder"),("lake","heaven"),("heaven","wind"),
    ("lake","earth"),("earth","wind"),("lake","water"),("water","wind"),
    ("lake","fire"),("fire","wind"),("thunder","thunder"),("mountain","mountain"),
    ("wind","mountain"),("thunder","lake"),("thunder","fire"),("fire","mountain"),
    ("wind","wind"),("lake","lake"),("wind","water"),("water","lake"),
    ("wind","lake"),("thunder","mountain"),("water","fire"),("fire","water"),
]


class IChingSystem(SymbolicSystem):
    id = "iching-zhouyi"
    version = "1"

    def units(self) -> tuple[SymbolicUnit, ...]:
        units = []
        for index, (name, archetype, pair) in enumerate(zip(_NAMES, _THEMES, _PAIRS), 1):
            upper, lower = pair
            line_pattern = _TRIGRAMS[lower] + _TRIGRAMS[upper]
            units.append(SymbolicUnit(
                id=f"hexagram-{index:02d}",
                number=index,
                name=name,
                archetype=archetype,
                keywords=tuple(part.strip() for part in archetype.split(",")),
                required_cues=(
                    f"canonical six-line pattern bottom-to-top: {line_pattern}",
                    f"upper trigram: {upper}",
                    f"lower trigram: {lower}",
                    f"hexagram identity: {name}",
                ),
                metadata={
                    "kind": "hexagram",
                    "traditional_name": name,
                    "upper_trigram": upper,
                    "lower_trigram": lower,
                    "line_pattern_bottom_to_top": line_pattern,
                },
            ))
        return tuple(units)
