"""Tests für die Geldlogik."""

from decimal import Decimal

import pytest

from kontor_budget.errors import ValidationError
from kontor_budget.money import parse_money, ratio, to_money


class TestParseMoney:
    def test_accepts_english_notation(self):
        assert parse_money("1234.56") == Decimal("1234.56")

    def test_accepts_german_notation(self):
        assert parse_money("1.234,56") == Decimal("1234.56")

    def test_strips_whitespace(self):
        assert parse_money("  42  ") == Decimal("42.00")

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            parse_money("")

    def test_rejects_negative(self):
        with pytest.raises(ValidationError):
            parse_money("-5")

    def test_rejects_text(self):
        with pytest.raises(ValidationError):
            parse_money("abc")

    def test_rounds_half_up(self):
        assert parse_money("10.005") == Decimal("10.01")


class TestToMoney:
    def test_float_does_not_inherit_binary_error(self):
        """Der eigentliche Grund für den Umweg über str.

        Decimal(0.1) wäre 0.1000000000000000055511151231257827.
        """
        assert to_money(0.1) == Decimal("0.10")

    def test_rejects_infinity(self):
        with pytest.raises(ValidationError):
            to_money(float("inf"))

    def test_rejects_unsupported_type(self):
        with pytest.raises(ValidationError):
            to_money([1, 2, 3])


class TestRatio:
    def test_returns_zero_on_zero_denominator(self):
        assert ratio(Decimal("100"), Decimal("0")) == Decimal("0")

    def test_divides_normally(self):
        assert ratio(Decimal("50"), Decimal("200")) == Decimal("0.25")


def test_decimal_avoids_the_classic_float_error():
    """Mit float wäre 0.1 + 0.2 gleich 0.30000000000000004."""
    assert to_money("0.1") + to_money("0.2") == Decimal("0.30")
