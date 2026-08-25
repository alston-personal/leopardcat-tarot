from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .decks import DeckRegistry


@dataclass(frozen=True)
class BrandPack:
    brand_id: str
    app_name: str
    short_name: str
    creator_line: str
    description: str
    share_title: dict[str, str]
    share_site_tag: dict[str, str]
    share_copy_template: dict[str, str]
    default_quote: dict[str, str]
    file_prefix: str

    def public_info(self) -> dict[str, Any]:
        return {
            "brand_id": self.brand_id,
            "app_name": self.app_name,
            "short_name": self.short_name,
            "creator_line": self.creator_line,
            "description": self.description,
            "share_title": self.share_title,
            "share_site_tag": self.share_site_tag,
            "share_copy_template": self.share_copy_template,
            "default_quote": self.default_quote,
            "file_prefix": self.file_prefix,
        }


class BrandRegistry:
    """Brand presentation contract, independent from Tarot method logic.

    A deck may use an explicit brand pack later. For now every custom deck gets a
    deterministic default pack synthesized from public deck metadata, while the
    built-in LeopardCat deck keeps its own first-party brand pack.
    """

    def __init__(self, decks: DeckRegistry) -> None:
        self.decks = decks

    def get(self, deck_id: str | None) -> BrandPack:
        deck = self.decks.get(deck_id)
        if deck.deck_id == "leopardcat":
            return BrandPack(
                brand_id="leopardcat",
                app_name="靈山靈貓・石虎塔羅",
                short_name="靈山靈貓",
                creator_line="LeopardCat Tarot",
                description="連結淺山靈魂，傾聽大師開示。讓石虎為你指引生命的方向。",
                share_title={"zh": "靈山靈貓・石虎塔羅", "en": "LeopardCat Tarot"},
                share_site_tag={"zh": "靈山靈貓・石虎塔羅", "en": "LeopardCat Tarot"},
                share_copy_template={"zh": "我在石虎塔羅抽到了：{card}", "en": "I drew {card} from LeopardCat Tarot"},
                default_quote={"zh": "與山靈連結，尋找內心的平靜。", "en": "Connect with the spirits, find your inner peace."},
                file_prefix="leopardcat-tarot",
            )

        creator = deck.creator.strip()
        creator_line = f"牌卡創作：{creator}" if creator else "專屬線上占卜"
        description = deck.description.strip() or (f"由 {creator} 創作的塔羅牌組。" if creator else f"{deck.name} 線上塔羅占卜。")
        return BrandPack(
            brand_id=f"deck:{deck.deck_id}",
            app_name=deck.name,
            short_name=deck.name,
            creator_line=creator_line,
            description=description,
            share_title={"zh": f"{deck.name}・塔羅指引", "en": f"{deck.name} Tarot Reading"},
            share_site_tag={"zh": creator_line, "en": f"Deck by {creator}" if creator else "Personal Tarot Deck"},
            share_copy_template={"zh": f"我在「{deck.name}」抽到了：{{card}}", "en": f"I drew {{card}} from {deck.name}"},
            default_quote={"zh": "聽見牌面，也聽見自己。", "en": "Listen to the cards, and to yourself."},
            file_prefix=deck.deck_id,
        )

    def public_info(self, deck_id: str | None) -> dict[str, Any]:
        return self.get(deck_id).public_info()
