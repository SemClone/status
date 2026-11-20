import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fetch_stats as fs  # noqa: E402


def rows(*triples):
    return {"data": [{"date": d, "category": c, "downloads": n} for d, c, n in triples]}


class Windows(unittest.TestCase):
    def test_headline_is_with_mirrors_not_both_categories_summed(self):
        m = fs.calculate_metrics_from_overall(rows(
            ("2026-11-18", "with_mirrors", 10), ("2026-11-18", "without_mirrors", 7)))
        self.assertEqual(m["last_day"], 10)
        self.assertEqual(m["last_day_without_mirrors"], 7)

    def test_week_is_seven_calendar_days_not_seven_data_points(self):
        # Days with no downloads have no row; an older day must not fill in.
        m = fs.calculate_metrics_from_overall(rows(
            ("2026-11-18", "with_mirrors", 1), ("2026-11-01", "with_mirrors", 100)))
        self.assertEqual(m["last_week"], 1)
        self.assertEqual(m["last_month"], 101)

    def test_no_data_is_none_not_zero(self):
        self.assertIsNone(fs.calculate_metrics_from_overall({})["last_day"])


class History(unittest.TestCase):
    def test_days_that_leave_the_api_window_stay_in_the_total(self):
        h = {"packages": {}}
        fs.merge_overall_into_history(h, "p", rows(("2026-01-01", "with_mirrors", 5),
                                                   ("2026-01-01", "without_mirrors", 3)))
        fs.merge_overall_into_history(h, "p", rows(("2026-07-01", "with_mirrors", 2),
                                                   ("2026-07-01", "without_mirrors", 1)))
        t = fs.totals_from_history(h, "p")
        self.assertEqual((t["total"], t["total_without_mirrors"]), (7, 4))
        self.assertEqual(t["total_since"], "2026-01-01")

    def test_a_revised_day_replaces_rather_than_adds(self):
        h = {"packages": {}}
        fs.merge_overall_into_history(h, "p", rows(("2026-07-01", "with_mirrors", 2)))
        fs.merge_overall_into_history(h, "p", rows(("2026-07-01", "with_mirrors", 9)))
        self.assertEqual(fs.totals_from_history(h, "p")["total"], 9)

    def test_failed_fetch_merges_nothing_and_keeps_totals(self):
        h = {"packages": {}}
        fs.merge_overall_into_history(h, "p", rows(("2026-07-01", "with_mirrors", 4)))
        self.assertEqual(fs.merge_overall_into_history(h, "p", {}), 0)
        self.assertEqual(fs.totals_from_history(h, "p")["total"], 4)

    def test_unreadable_history_file_raises_instead_of_resetting(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"oops": 1}, f)
        try:
            with self.assertRaises(ValueError):
                fs.load_history(f.name)
        finally:
            os.unlink(f.name)

    def test_missing_history_file_is_empty(self):
        self.assertEqual(fs.load_history("/nonexistent/history.json"), {"packages": {}})


if __name__ == "__main__":
    unittest.main()
