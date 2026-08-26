from __future__ import annotations

import random
from typing import Any

from .core import DivinationError


# Petit Lenormand 36-card canonical order. Meanings are concise public-domain style keywords,
# intentionally not copied from any proprietary deck text.
LENORMAND_CARDS: list[dict[str, Any]] = [
    {"id":"rider","number":1,"title":{"zh-TW":"騎士","en":"Rider"},"icon":"🐎","keywords":["消息","到來","行動"],"polarity":1},
    {"id":"clover","number":2,"title":{"zh-TW":"幸運草","en":"Clover"},"icon":"🍀","keywords":["小幸運","機會","短暫"],"polarity":1},
    {"id":"ship","number":3,"title":{"zh-TW":"船","en":"Ship"},"icon":"⛵","keywords":["遠行","距離","探索"],"polarity":0},
    {"id":"house","number":4,"title":{"zh-TW":"房屋","en":"House"},"icon":"🏠","keywords":["家庭","穩定","基礎"],"polarity":1},
    {"id":"tree","number":5,"title":{"zh-TW":"樹","en":"Tree"},"icon":"🌳","keywords":["成長","健康","長期"],"polarity":1},
    {"id":"clouds","number":6,"title":{"zh-TW":"雲","en":"Clouds"},"icon":"☁️","keywords":["混亂","不確定","遮蔽"],"polarity":-1},
    {"id":"snake","number":7,"title":{"zh-TW":"蛇","en":"Snake"},"icon":"🐍","keywords":["迂迴","複雜","誘惑"],"polarity":-1},
    {"id":"coffin","number":8,"title":{"zh-TW":"棺木","en":"Coffin"},"icon":"⚰️","keywords":["結束","停滯","轉換"],"polarity":-1},
    {"id":"bouquet","number":9,"title":{"zh-TW":"花束","en":"Bouquet"},"icon":"💐","keywords":["禮物","喜悅","魅力"],"polarity":1},
    {"id":"scythe","number":10,"title":{"zh-TW":"鐮刀","en":"Scythe"},"icon":"✂️","keywords":["突然切斷","決斷","風險"],"polarity":-1},
    {"id":"whip","number":11,"title":{"zh-TW":"鞭子","en":"Whip"},"icon":"🪢","keywords":["衝突","重複","壓力"],"polarity":-1},
    {"id":"birds","number":12,"title":{"zh-TW":"鳥","en":"Birds"},"icon":"🐦","keywords":["對話","焦慮","短訊"],"polarity":0},
    {"id":"child","number":13,"title":{"zh-TW":"孩子","en":"Child"},"icon":"🧒","keywords":["新開始","小規模","單純"],"polarity":1},
    {"id":"fox","number":14,"title":{"zh-TW":"狐狸","en":"Fox"},"icon":"🦊","keywords":["策略","警覺","工作"],"polarity":-1},
    {"id":"bear","number":15,"title":{"zh-TW":"熊","en":"Bear"},"icon":"🐻","keywords":["力量","資源","權威"],"polarity":0},
    {"id":"stars","number":16,"title":{"zh-TW":"星星","en":"Stars"},"icon":"⭐","keywords":["方向","希望","清晰"],"polarity":1},
    {"id":"stork","number":17,"title":{"zh-TW":"鸛鳥","en":"Stork"},"icon":"🕊️","keywords":["改變","搬遷","改善"],"polarity":1},
    {"id":"dog","number":18,"title":{"zh-TW":"狗","en":"Dog"},"icon":"🐕","keywords":["朋友","忠誠","支持"],"polarity":1},
    {"id":"tower","number":19,"title":{"zh-TW":"高塔","en":"Tower"},"icon":"🏛️","keywords":["制度","距離","獨立"],"polarity":0},
    {"id":"garden","number":20,"title":{"zh-TW":"花園","en":"Garden"},"icon":"🌷","keywords":["社交","公開","群體"],"polarity":1},
    {"id":"mountain","number":21,"title":{"zh-TW":"山","en":"Mountain"},"icon":"⛰️","keywords":["阻礙","延遲","挑戰"],"polarity":-1},
    {"id":"crossroads","number":22,"title":{"zh-TW":"岔路","en":"Crossroads"},"icon":"🛤️","keywords":["選擇","多路徑","決策"],"polarity":0},
    {"id":"mice","number":23,"title":{"zh-TW":"老鼠","en":"Mice"},"icon":"🐁","keywords":["耗損","焦慮","流失"],"polarity":-1},
    {"id":"heart","number":24,"title":{"zh-TW":"心","en":"Heart"},"icon":"❤️","keywords":["愛","熱情","真心"],"polarity":1},
    {"id":"ring","number":25,"title":{"zh-TW":"戒指","en":"Ring"},"icon":"💍","keywords":["承諾","契約","循環"],"polarity":1},
    {"id":"book","number":26,"title":{"zh-TW":"書","en":"Book"},"icon":"📕","keywords":["知識","秘密","學習"],"polarity":0},
    {"id":"letter","number":27,"title":{"zh-TW":"信件","en":"Letter"},"icon":"✉️","keywords":["文件","文字訊息","通知"],"polarity":0},
    {"id":"man","number":28,"title":{"zh-TW":"男性人物","en":"Man"},"icon":"👤","keywords":["男性人物","主動角色","焦點人物"],"polarity":0},
    {"id":"woman","number":29,"title":{"zh-TW":"女性人物","en":"Woman"},"icon":"👤","keywords":["女性人物","接收角色","焦點人物"],"polarity":0},
    {"id":"lily","number":30,"title":{"zh-TW":"百合","en":"Lily"},"icon":"🪷","keywords":["成熟","和平","倫理"],"polarity":1},
    {"id":"sun","number":31,"title":{"zh-TW":"太陽","en":"Sun"},"icon":"☀️","keywords":["成功","活力","明朗"],"polarity":1},
    {"id":"moon","number":32,"title":{"zh-TW":"月亮","en":"Moon"},"icon":"🌙","keywords":["情緒","名聲","直覺"],"polarity":1},
    {"id":"key","number":33,"title":{"zh-TW":"鑰匙","en":"Key"},"icon":"🔑","keywords":["解答","確定","關鍵"],"polarity":1},
    {"id":"fish","number":34,"title":{"zh-TW":"魚","en":"Fish"},"icon":"🐟","keywords":["金流","資源流動","自主"],"polarity":1},
    {"id":"anchor","number":35,"title":{"zh-TW":"錨","en":"Anchor"},"icon":"⚓","keywords":["穩固","工作","持久"],"polarity":1},
    {"id":"cross","number":36,"title":{"zh-TW":"十字架","en":"Cross"},"icon":"✝️","keywords":["負擔","責任","考驗"],"polarity":-1},
]

SPREADS: dict[str, dict[str, Any]] = {
    "yes_no": {"name":"是／否", "count":1, "positions":[("answer","答案核心")]},
    "three": {"name":"三張牌", "count":3, "positions":[("past","前因"),("present","現在"),("future","走向")]},
    "five": {"name":"五張線性牌陣", "count":5, "positions":[("p1","背景"),("p2","推力"),("center","核心"),("p4","阻力／助力"),("p5","走向")]},
    "box9": {"name":"九宮格", "count":9, "positions":[
        ("r1c1","左上"),("r1c2","上方"),("r1c3","右上"),
        ("r2c1","左方"),("center","中心"),("r2c3","右方"),
        ("r3c1","左下"),("r3c2","下方"),("r3c3","右下"),
    ]},
}


def _title(card: dict[str, Any]) -> str:
    return str((card.get("title") or {}).get("zh-TW") or card.get("id"))


def _adjacent_pairs(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    for i in range(len(cards) - 1):
        left, right = cards[i], cards[i + 1]
        pairs.append({
            "left": left["card_id"], "right": right["card_id"],
            "reading_rule": "左牌提供情境／修飾，右牌提供主題延伸／結果",
            "phrase": f"{left['keywords'][0]} → {right['keywords'][0]}",
            "tone": left["polarity"] + right["polarity"],
        })
    return pairs


class LenormandMethod:
    method_id = "lenormand"

    def generate(self, *, input_data: dict[str, Any], question: str, rng: random.Random) -> dict[str, Any]:
        spread_id = str(input_data.get("spread") or "three")
        if spread_id not in SPREADS:
            raise DivinationError(f"unsupported lenormand spread: {spread_id}")
        spread = SPREADS[spread_id]
        picked = rng.sample(LENORMAND_CARDS, int(spread["count"]))
        results: list[dict[str, Any]] = []
        for card, (position, label) in zip(picked, spread["positions"]):
            results.append({
                "card_id": card["id"], "number": card["number"], "title": card["title"],
                "icon": card["icon"], "keywords": list(card["keywords"]), "polarity": card["polarity"],
                "position": position, "position_label": label,
            })

        structure: dict[str, Any] = {
            "combination_priority": True,
            "adjacent_pairs": _adjacent_pairs(results),
            "polarity_score": sum(x["polarity"] for x in results),
        }
        if spread_id == "yes_no":
            score = structure["polarity_score"]
            structure["answer_tendency"] = "yes" if score > 0 else ("no" if score < 0 else "unclear")
        elif spread_id == "five":
            structure["center_card"] = results[2]["card_id"]
            structure["reading_order"] = ["center", "left_context", "right_development", "full_line"]
        elif spread_id == "box9":
            structure["center_card"] = results[4]["card_id"]
            structure["rows"] = [[x["card_id"] for x in results[0:3]], [x["card_id"] for x in results[3:6]], [x["card_id"] for x in results[6:9]]]
            structure["columns"] = [[results[i]["card_id"] for i in (0,3,6)], [results[i]["card_id"] for i in (1,4,7)], [results[i]["card_id"] for i in (2,5,8)]]
            structure["diagonals"] = [[results[i]["card_id"] for i in (0,4,8)], [results[i]["card_id"] for i in (2,4,6)]]
            structure["reading_order"] = ["center", "middle_row", "middle_column", "diagonals", "outer_context"]

        return {
            "method": "lenormand",
            "deck": {"deck_id":"petit-lenormand-36", "name":"Petit Lenormand 36", "card_count":36, "source":"builtin"},
            "spread": spread_id,
            "spread_name": spread["name"],
            "cards": results,
            "structure": structure,
            "rules": {
                "without_replacement": True,
                "reversals": False,
                "combination_reading": True,
                "position_and_adjacency_are_semantic": True,
            },
        }


def public_method_info() -> dict[str, Any]:
    return {
        "method_id": "lenormand",
        "name": "雷諾曼 Lenormand",
        "description": "36 張符號牌，以位置、相鄰組合與整體結構優先解讀。",
        "spreads": [{"id": k, "name": v["name"], "card_count": v["count"]} for k, v in SPREADS.items()],
    }
