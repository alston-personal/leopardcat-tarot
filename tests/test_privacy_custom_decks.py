import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "website"))

from divination.core import ReadingRequest, MethodRegistry, PersonaRegistry, DivinationEngine
from divination.decks import DeckRegistry
from divination.personas import GenericMasterPersona
from divination.sessions import ReadingSessionStore
from divination.tarot import TarotMethod


class CustomDeckTests(unittest.TestCase):
    def test_22_card_deck_works_without_core_changes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            default_manifest = root / "default.json"
            default_manifest.write_text("[]", encoding="utf-8")
            deck_dir = root / "custom" / "artist-major-arcana"
            deck_dir.mkdir(parents=True)
            cards = [{
                "id": f"card-{i:03d}",
                "title": {"zh": f"牌{i}"},
                "meanings": {"upright": f"正位{i}", "reversed": f"逆位{i}"},
                "image": f"/fake/{i}.webp",
            } for i in range(1, 23)]
            (deck_dir / "deck.json").write_text(json.dumps({
                "name": "Artist Major Arcana", "creator": "Artist", "reversals": True, "cards": cards
            }, ensure_ascii=False), encoding="utf-8")

            decks = DeckRegistry(default_manifest, root / "custom")
            methods = MethodRegistry(); methods.register(TarotMethod(decks))
            personas = PersonaRegistry(); personas.register(GenericMasterPersona())
            engine = DivinationEngine(methods, personas)
            result = engine.prepare(ReadingRequest(
                method="tarot", persona="master", question="未來如何？",
                input={"deck_id": "artist-major-arcana", "spread": "three_card"}, seed="22-card-proof"
            )).method_result
            self.assertEqual(result["deck"]["card_count"], 22)
            self.assertEqual(len(result["cards"]), 3)
            self.assertEqual(len({c["card_id"] for c in result["cards"]}), 3)

    def test_deck_can_disable_reversals(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            default_manifest = root / "default.json"; default_manifest.write_text("[]", encoding="utf-8")
            deck_dir = root / "custom" / "no-reverse"; deck_dir.mkdir(parents=True)
            cards = [{"id": f"c{i}", "title": {"zh": str(i)}, "meanings": {"upright": "x"}} for i in range(5)]
            (deck_dir / "deck.json").write_text(json.dumps({"name":"No Reverse","reversals":False,"cards":cards}), encoding="utf-8")
            tarot = TarotMethod(DeckRegistry(default_manifest, root / "custom"))
            import random
            result = tarot.generate(input_data={"deck_id":"no-reverse","spread":"three_card","reversal_rate":1}, question="x", rng=random.Random(1))
            self.assertTrue(all(c["orientation"] == "upright" for c in result["cards"]))


class PrivacySessionTests(unittest.TestCase):
    def test_session_persists_symbols_not_question_or_answer(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "sessions.sqlite3"
            store = ReadingSessionStore(db, ttl_seconds=60)
            issued = store.create(
                reading_id="rd_test", method="tarot", persona="master", deck_id="artist-major-arcana",
                method_result={"method":"tarot","cards":[{"card_id":"c1"}]},
            )
            loaded = store.get("rd_test", issued["session_token"])
            self.assertEqual(loaded["method_result"]["cards"][0]["card_id"], "c1")
            raw = db.read_bytes()
            self.assertNotIn("我的秘密問題".encode(), raw)
            self.assertNotIn("大師回答".encode(), raw)
            self.assertNotIn(issued["session_token"].encode(), raw)


if __name__ == "__main__":
    unittest.main()
