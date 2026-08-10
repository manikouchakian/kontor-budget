"""Auswertung eines Monats und Vergleich zweier Monate.

Ausschließlich reine Funktionen: gleiche Eingabe, gleiche Ausgabe, keine
Seiteneffekte, kein Datei- oder Konsolenzugriff. Deshalb ist dieses Modul
vollständig ohne Testdoubles testbar.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from kontor_budget.config import SCORE_THRESHOLDS, TARGET_SAVINGS_RATE
from kontor_budget.errors import ValidationError
from kontor_budget.models import Comparison, MonthEntry, Summary
from kontor_budget.money import ZERO, Money, ratio, to_money

HUNDRED = Decimal("100")


def clamp(value: Decimal, low: Decimal, high: Decimal) -> Decimal:
    """Begrenzt einen Wert auf das Intervall ``[low, high]``."""
    return max(low, min(value, high))


def calculate_summary(entry: MonthEntry) -> Summary:
    """Berechnet Gesamtausgaben, Rest, Kategorieanteile und Sparquote."""
    if entry.income < ZERO:
        raise ValidationError("Income cannot be negative")
    if any(value < ZERO for value in entry.expenses.values()):
        raise ValidationError("Expenses cannot be negative")

    total = entry.total_expenses
    remaining = entry.income - total

    percentages = {
        category: ratio(value, entry.income) * HUNDRED
        for category, value in entry.expenses.items()
    }

    return Summary(
        total_expenses=total,
        remaining=remaining,
        percentages=percentages,
        savings_rate=ratio(remaining, entry.income),
    )


def calculate_score(
    income: Money,
    remaining: Money,
    target_rate: Decimal = TARGET_SAVINGS_RATE,
) -> int:
    """Bewertet die Sparquote auf einer Skala von 0 bis 100.

    100 bedeutet, dass die Zielsparquote erreicht oder übertroffen wurde.
    Ohne Einkommen oder ohne Überschuss ist das Ergebnis 0.
    """
    if target_rate <= 0:
        raise ValidationError("Target savings rate must be positive")

    income = to_money(income)
    remaining = to_money(remaining)

    if income <= ZERO or remaining <= ZERO:
        return 0

    score = (ratio(remaining, income) / target_rate) * HUNDRED
    bounded = clamp(score, Decimal("0"), HUNDRED)

    return int(bounded.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def score_label(score: int) -> str:
    """Übersetzt einen Score in ein Label."""
    for threshold, label in SCORE_THRESHOLDS:
        if score >= threshold:
            return label
    return SCORE_THRESHOLDS[-1][1]


def compare_months(current: MonthEntry, previous: MonthEntry) -> Comparison:
    """Vergleicht zwei Monate.

    Beide laufen durch dieselbe Auswertungslogik, damit der Vergleich
    konsistent bleibt. Kategorien, die nur in einem der beiden Monate
    vorkommen, werden im jeweils anderen als null behandelt.
    """
    current_summary = calculate_summary(current)
    previous_summary = calculate_summary(previous)

    categories = set(current.expenses) | set(previous.expenses)
    category_diff = {
        category: current.expenses.get(category, ZERO)
        - previous.expenses.get(category, ZERO)
        for category in categories
    }

    return Comparison(
        income_diff=current.income - previous.income,
        total_expenses_diff=(
            current_summary.total_expenses - previous_summary.total_expenses
        ),
        remaining_diff=current_summary.remaining - previous_summary.remaining,
        savings_rate_diff=(current_summary.savings_rate - previous_summary.savings_rate),
        category_diff=category_diff,
    )
