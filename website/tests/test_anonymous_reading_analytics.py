import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from divination.analytics import ReadingAnalyticsStore, classify_question, normalize_source


class TestAnonymousReadingAnalytics(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / 'analytics.sqlite3'
        self.store = ReadingAnalyticsStore(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def sample_result(self):
        return {
            'deck': {'deck_id': 'leopardcat'},
            'spread': 'relationship',
            'spread_plan': {'intent': 'relationship'},
            'cards': [
                {'card_id': 'card-a', 'orientation': 'upright', 'position': 'self'},
                {'card_id': 'card-b', 'orientation': 'reversed', 'position': 'other'},
            ],
            'rules': {'draw_mode': 'manual'},
        }

    def test_question_classification_is_coarse_only(self):
        self.assertEqual(classify_question('我跟對方的感情會如何？', self.sample_result()), 'love_relationship')
        self.assertEqual(classify_question('我的投資和收入接下來如何？', {'spread_plan': {'intent': 'guidance'}}), 'money')
        self.assertEqual(classify_question('Should I take job A or B?', {'spread_plan': {'intent': 'decision'}}), 'career_study')

    def test_unknown_source_collapses_to_other(self):
        self.assertEqual(normalize_source('threads'), 'threads')
        self.assertEqual(normalize_source('https://threads.net/@person/post/secret'), 'other')

    def test_record_never_has_question_answer_or_identity_columns(self):
        self.store.record_reading(
            source='threads',
            question_category='love_relationship',
            method='tarot',
            method_result=self.sample_result(),
            language='zh-TW',
            persona_id='master',
        )
        with sqlite3.connect(self.db) as conn:
            event_columns = [row[1] for row in conn.execute('PRAGMA table_info(reading_analytics)')]
            card_columns = [row[1] for row in conn.execute('PRAGMA table_info(reading_cards)')]
            row = conn.execute('SELECT * FROM reading_analytics').fetchone()
        forbidden = {'question', 'answer', 'ip', 'referrer', 'reading_id', 'session_id', 'user_id', 'visitor_id'}
        self.assertTrue(row)
        self.assertFalse(forbidden.intersection(event_columns))
        self.assertFalse(forbidden.intersection(card_columns))

    def test_summary_contains_only_aggregates(self):
        self.store.record_reading(
            source='threads',
            question_category='love_relationship',
            method='tarot',
            method_result=self.sample_result(),
            language='zh-TW',
            persona_id='master',
        )
        summary = self.store.summary(days=30)
        serialized = json.dumps(summary, ensure_ascii=False)
        self.assertEqual(summary['total_readings'], 1)
        self.assertEqual(summary['by_source']['threads'], 1)
        self.assertEqual(summary['by_category']['love_relationship'], 1)
        self.assertEqual(summary['by_spread']['relationship'], 1)
        self.assertIn('card-a', serialized)
        self.assertNotIn('question', set(summary.keys()))
        self.assertFalse(summary['privacy']['question_stored'])
        self.assertFalse(summary['privacy']['answer_stored'])


if __name__ == '__main__':
    unittest.main()
