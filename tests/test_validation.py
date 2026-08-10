"""Tests für Monatsvalidierung und Datenmodelle."""

from decimal import Decimal

import pytest

from kontor_budget.errors import ValidationError
from kontor_budget.models import Comparison, MonthEntry
from kontor_budget.validation import previous_month, validate_month


class TestValidateMonth:
    def test_accepts_valid_month(self):
        assert validate_month("2026-08") == "2026-08"

    def test_strips_whitespace(self):
        assert validate_month("  2026-01  ") == "2026-01"

    @pytest.mark.parametrize(
        "value",
        ["2026-13", "2026-00", "26-08", "2026-8", "2026", "2026-08-01", "abcd-ef"],
    )
    def test_rejects_invalid_formats(self, value):
        with pytest.raises(ValidationError):
            validate_month(value)

    def test_rejects_non_string(self):
        with pytest.raises(ValidationError):
            validate_month(202608)

    def test_rejects_year_out_of_range(self):
        with pytest.raises(ValidationError):
            validate_month("1899-01")


class TestPreviousMonth:
    def test_handles_january(self):
        """Der Jahreswechsel ist der Fall, der am häufigsten vergessen wird."""
        assert previous_month("2026-01") == "2025-12"

    def test_handles_normal_month(self):
        assert previous_month("2026-08") == "2026-07"


class TestMonthEntry:
    def test_normalises_input_to_money(self):
        entry = MonthEntry(income=1000, expenses={"rent": "450.5"})
        assert entry.income == Decimal("1000.00")
        assert entry.expenses["rent"] == Decimal("450.50")

    def test_total_expenses_sums_all_categories(self):
        entry = MonthEntry(income=1000, expenses={"rent": 400, "food": 100})
        assert entry.total_expenses == Decimal("500.00")

    def test_total_expenses_is_zero_without_expenses(self):
        assert MonthEntry(income=1000).total_expenses == Decimal("0.00")

    def test_is_immutable(self):
        """Ein gebuchter Monat wird nicht nachträglich verändert."""
        entry = MonthEntry(income=1000, expenses={"rent": 400})

        with pytest.raises(AttributeError):
            entry.income = Decimal("2000")

        with pytest.raises(TypeError):
            entry.expenses["rent"] = Decimal("1")


class TestComparison:
    def test_biggest_changes_sorts_by_absolute_value(self):
        comparison = Comparison(
            income_diff=Decimal("0"),
            total_expenses_diff=Decimal("0"),
            remaining_diff=Decimal("0"),
            savings_rate_diff=Decimal("0"),
            category_diff={
                "rent": Decimal("10"),
                "food": Decimal("-90"),
                "gas": Decimal("50"),
            },
        )

        assert [name for name, _ in comparison.biggest_changes()] == ["food", "gas"]
