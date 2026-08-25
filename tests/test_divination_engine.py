import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "website"))

from divination import ReadingRequest, build_default_engine


class DivinationEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = build_default_engine(ROOT / "website")

    def test_single_draw_has_orientation(self):
        reading = self.engine.prepare(ReadingRequest(
            method="tarot",
            persona="leopardcat",
            question="我現在需要注意什麼？",
            input={"spread": "single"},
            seed="same-seed",
        ))
        cards = reading.method_result["cards"]
        self.assertEqual(len(cards), 1)
        self.assertIn(cards[0]["orientation"], {"upright", "reversed"})
        self.assertTrue(cards[0]["meaning"])

    def test_seed_reproduces_symbolic_result(self):
        req = ReadingRequest(
            method="tarot",
            persona="leopardcat",
            question="接下來三個階段如何發展？",
            input={"spread": "three_card"},
            seed="reproducible",
        )
        a = self.engine.prepare(req).method_result
        b = self.engine.prepare(req).method_result
        self.assertEqual(a, b)
        self.assertEqual(len({c["card_id"] for c in a["cards"]}), 3)

    def test_reversal_rate_is_enforced(self):
        req = ReadingRequest(
            method="tarot",
            persona="leopardcat",
            question="測試逆位",
            input={"spread": "three_card", "reversal_rate": 1.0},
            seed="all-reversed",
        )
        result = self.engine.prepare(req).method_result
        self.assertTrue(all(c["orientation"] == "reversed" for c in result["cards"]))

    def test_auto_decision_spread(self):
        req = ReadingRequest(
            method="tarot",
            persona="master",
            question="我該不該換工作？",
            input={"spread": "auto"},
            seed="decision",
        )
        result = self.engine.prepare(req).method_result
        self.assertEqual(result["spread"], "decision")
        self.assertEqual(len(result["cards"]), 3)


if __name__ == "__main__":
    unittest.main()
