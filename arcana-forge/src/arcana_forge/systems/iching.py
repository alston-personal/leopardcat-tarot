from __future__ import annotations

from arcana_forge.schema import SymbolicUnit
from arcana_forge.systems.base import SymbolicSystem

_NAMES = [
"乾","坤","屯","蒙","需","訟","師","比","小畜","履","泰","否","同人","大有","謙","豫",
"隨","蠱","臨","觀","噬嗑","賁","剝","復","無妄","大畜","頤","大過","坎","離","咸","恆",
"遯","大壯","晉","明夷","家人","睽","蹇","解","損","益","夬","姤","萃","升","困","井",
"革","鼎","震","艮","漸","歸妹","豐","旅","巽","兌","渙","節","中孚","小過","既濟","未濟"
]
_THEMES = [
"creative heaven and active strength","receptive earth and yielding support","difficulty at beginning","youthful learning",
"waiting and nourishment","conflict and contention","organized collective force","union and alliance","small restraint","careful conduct",
"peace and exchange","stagnation and blockage","fellowship","great possession","modesty","enthusiasm"
]


class IChingSystem(SymbolicSystem):
    id = "iching-zhouyi"
    version = "1"

    def units(self) -> tuple[SymbolicUnit, ...]:
        units = []
        for index,name in enumerate(_NAMES, 1):
            archetype = _THEMES[index-1] if index <= len(_THEMES) else f"Zhouyi hexagram {index}: preserve the canonical identity of {name}"
            units.append(SymbolicUnit(
                id=f"hexagram-{index:02d}",
                number=index,
                name=name,
                archetype=archetype,
                keywords=tuple(part.strip() for part in archetype.replace(" and ", ",").split(",")),
                required_cues=(f"canonical six-line hexagram #{index}", f"hexagram identity: {name}"),
                metadata={"kind":"hexagram","traditional_name":name},
            ))
        return tuple(units)
