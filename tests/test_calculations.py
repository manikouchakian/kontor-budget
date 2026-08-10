"""Tests für die Berechnungen."""

from decimal import Decimal

import pytest

from kontor_budget.calculations import (
    calculate_score,
    calculate_summary,
    clamp,
    compare_months,
    score_label,
)
from kontor_budget.errors import ValidationError
from kontor_budget.models import MonthEntry


class TestCalculateSummary:
    def test_empty_expenses(self):
        """Regressionstest.

        In der ersten Fassung stand die Berechnung der Sparquote innerhalb
        der Kategorien-Schleife. Ohne Ausgaben lief die Schleife nie und die
        Variable war nie definiert - UnboundLocalError.
        """
        summary = calculate_summary(MonthEntry(income=1000))

        assert summary.total_expenses == Decimal("0.00")
        assert summary.remaining == Decimal("1000.00")
        assert summary.savings_rate == Decimal("1")

    def test_percentages_and_savings_rate(self):
        summary = calculate_summary(
            MonthEntry(income=1000, expenses={"rent": 400, "food": 100})
        )

        assert summary.total_expenses == Decimal("500.00")
        assert summary.remaining == Decimal("500.00")
        assert summary.percentages["rent"] == Decimal("40")
        assert summary.savings_rate == Decimal("0.5")

    def test_zero_income_yields_zero_rate(self):
        summary = calculate_summary(MonthEntry(income=0, expenses={"rent": 100}))

        assert summary.remaining == Decimal("-100.00")
        assert summary.savings_rate == Decimal("0")
        assert summary.percentages["rent"] == Decimal("0")

    def test_rejects_negative_expenses(self):
        with pytest.raises(ValidationError):
            calculate_summary(MonthEntry(income=1000, expenses={"rent": -50}))


class TestCalculateScore:
    def test_zero_without_income(self):
        assert calculate_score(Decimal("0"), Decimal("0")) == 0

    def test_zero_without_surplus(self):
        assert calculate_score(Decimal("1000"), Decimal("-50")) == 0

    def test_caps_at_hundred(self):
        """Sparquote 50 Prozent bei Ziel 30 - gedeckelt auf 100, nicht 166."""
        assert calculate_score(Decimal("1000"), Decimal("500")) == 100

    def test_exactly_on_target(self):
        assert calculate_score(Decimal("1000"), Decimal("300")) == 100

    def test_half_of_target(self):
        assert calculate_score(Decimal("1000"), Decimal("150")) == 50

    def test_rejects_non_positive_target(self):
        with pytest.raises(ValidationError):
            calculate_score(Decimal("1000"), Decimal("300"), Decimal("0"))


class TestScoreLabel:
    @pytest.mark.parametrize(
        ("score", "expected"),
        [
            (0, "Weak"),
            (39, "Weak"),
            (40, "OK"),
            (59, "OK"),
            (60, "Good"),
            (79, "Good"),
            (80, "Excellent"),
            (100, "Excellent"),
        ],
    )
    def test_boundaries(self, score, expected):
        assert score_label(score) == expected


class TestCompareMonths:
    def test_category_present_in_only_one_month(self):
        """Eine Kategorie darf beim Vergleich nicht verschwinden."""
        current = MonthEntry(income=1000, expenses={"rent": 400})
        previous = MonthEntry(income=1000, expenses={"gas": 50})

        result = compare_months(current, previous)

        assert result.category_diff["rent"] == Decimal("400.00")
        assert result.category_diff["gas"] == Decimal("-50.00")

    def test_diffs_are_current_minus_previous(self):
        current = MonthEntry(income=1200, expenses={"rent": 400})
        previous = MonthEntry(income=1000, expenses={"rent": 500})

        result = compare_months(current, previous)

        assert result.income_diff == Decimal("200.00")
        assert result.total_expenses_diff == Decimal("-100.00")
        assert result.remaining_diff == Decimal("300.00")

    def test_empty_previous_month(self):
        result = compare_months(
            MonthEntry(income=1000, expenses={"rent": 400}),
            MonthEntry(income=0),
        )

        assert result.income_diff == Decimal("1000.00")
        assert result.savings_rate_diff == Decimal("0.6")


class TestClamp:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(-5, 0), (0, 0), (50, 50), (100, 100), (150, 100)],
    )
    def test_bounds(self, value, expected):
        result = clamp(Decimal(value), Decimal("0"), Decimal("100"))
        assert result == Decimal(expected)
