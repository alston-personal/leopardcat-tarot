import tempfile
import unittest
from pathlib import Path

from divination.site_analytics import SCHEMA, SiteAnalyticsStore


class SiteAnalyticsStoreTests(unittest.TestCase):
    def make_store(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return SiteAnalyticsStore(Path(tmp.name) / "site.sqlite3")

    def payload(self, **changes):
        data = {
            "schema": SCHEMA,
            "site": "studio-web",
            "event_type": "page_view",
            "page_key": "agentos",
            "source": "threads",
            "language": "zh",
            "device_class": "mobile",
        }
        data.update(changes)
        return data

    def test_records_only_allowlisted_fields(self):
        store = self.make_store()
        event_id = store.record(self.payload())
        self.assertTrue(event_id)
        summary = store.summary(days=30, site="studio-web")
        self.assertEqual(summary["total_events"], 1)
        self.assertEqual(summary["by_source"], {"threads": 1})
        self.assertFalse(summary["privacy"]["persistent_visitor_id"])

    def test_rejects_free_form_or_identity_fields(self):
        store = self.make_store()
        for field in ("referrer", "ip", "question", "visitor_id", "user_agent"):
            with self.subTest(field=field):
                data = self.payload()
                data[field] = "should-not-be-stored"
                with self.assertRaisesRegex(ValueError, "analytics_field_not_allowed"):
                    store.record(data)

    def test_rejects_invalid_schema_event_and_keys(self):
        store = self.make_store()
        with self.assertRaises(ValueError):
            store.record(self.payload(schema="wrong"))
        with self.assertRaises(ValueError):
            store.record(self.payload(event_type="arbitrary"))
        with self.assertRaises(ValueError):
            store.record(self.payload(page_key="contains spaces and free text"))

    def test_summary_supports_funnel_dimensions(self):
        store = self.make_store()
        store.record(self.payload(event_type="project_open", project="agentos"))
        store.record(self.payload(event_type="cta_click", project="agentos", action="open-github"))
        store.record(self.payload(event_type="funnel_step", project="agentos", step="demo-opened"))
        summary = store.summary(days=30, site="studio-web")
        self.assertEqual(summary["by_event"]["project_open"], 1)
        self.assertEqual(summary["by_project"]["agentos"], 3)
        self.assertEqual(summary["by_action"]["open-github"], 1)
        self.assertEqual(summary["by_step"]["demo-opened"], 1)


if __name__ == "__main__":
    unittest.main()
