"""Tests für Persistenz und Berichtsformatierung."""

from decimal import Decimal

from kontor_budget.calculations import calculate_score, calculate_summary
from kontor_budget.models import MonthEntry
from kontor_budget.report import format_category, format_money, format_report
from kontor_budget.storage import load_data, save_data


class TestStorage:
    def test_roundtrip_preserves_exact_amounts(self, tmp_path):
        """Der Kern der Speicherentscheidung.

        Würden Beträge als JSON-Zahlen abgelegt, käme 0.10 unter Umständen
        als 0.1000000000000000055 zurück.
        """
        path = tmp_path / "data.json"
        original = {
            "2026-08": MonthEntry(
                income="1234.56",
                expenses={"rent": "0.10", "food": "0.20"},
            )
        }

        save_data(original, path)
        loaded = load_data(path)

        assert loaded["2026-08"].income == Decimal("1234.56")
        assert loaded["2026-08"].total_expenses == Decimal("0.30")

    def test_missing_file_returns_empty(self, tmp_path):
        assert load_data(tmp_path / "nope.json") == {}

    def test_broken_file_returns_empty(self, tmp_path):
        path = tmp_path / "data.json"
        path.write_text("{ not json", encoding="utf-8")
        assert load_data(path) == {}

    def test_non_dict_payload_returns_empty(self, tmp_path):
        path = tmp_path / "data.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        assert load_data(path) == {}

    def test_skips_unusable_entries(self, tmp_path):
        path = tmp_path / "data.json"
        path.write_text(
            '{"2026-07": "broken", "2026-08": {"income": "100", "expenses": {}}}',
            encoding="utf-8",
        )

        loaded = load_data(path)

        assert "2026-07" not in loaded
        assert loaded["2026-08"].income == Decimal("100.00")

    def test_no_temp_file_left_behind(self, tmp_path):
        path = tmp_path / "data.json"
        save_data({"2026-08": MonthEntry(income=100)}, path)
        assert list(tmp_path.glob("*.tmp")) == []


class TestReport:
    def test_format_money_uses_thousands_separator(self):
        assert format_money(Decimal("1234.5")) == "1,234.50"

    def test_format_category_replaces_underscore(self):
        """In der ersten Fassung wurde '-' ersetzt statt '_'."""
        assert format_category("health_insurance") == "Health Insurance"

    def test_report_without_comparison(self):
        entry = MonthEntry(income=1000, expenses={"rent": 400})
        summary = calculate_summary(entry)
        score = calculate_score(entry.income, summary.remaining)

        text = format_report("2026-08", entry, summary, score)

        assert "Month: 2026-08" in text
        assert "No previous month data to compare." in text
        assert "Health Insurance" in text

    def test_report_includes_unknown_categories(self):
        entry = MonthEntry(income=1000, expenses={"travel": 200})
        summary = calculate_summary(entry)

        text = format_report("2026-08", entry, summary, 100)

        assert "Travel" in text
