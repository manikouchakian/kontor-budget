"""Formatierung des Berichts.

Enthält keine Berechnungen. Nimmt fertige Werte entgegen und macht daraus
Text. Dadurch lässt sich die Ausgabe ändern, ohne die Logik anzufassen.
"""

from __future__ import annotations

from decimal import Decimal

from kontor_budget.calculations import score_label
from kontor_budget.config import CATEGORIES
from kontor_budget.models import Comparison, MonthEntry, Summary
from kontor_budget.money import ZERO, Money

HUNDRED = Decimal("100")


def format_money(value: Money) -> str:
    """``1234.5`` wird zu ``1,234.50``."""
    return f"{value:,.2f}"


def format_percent(value: Decimal) -> str:
    """``21.42`` wird zu ``21.4%``."""
    return f"{value:.1f}%"


def format_category(category: str) -> str:
    """``health_insurance`` wird zu ``Health Insurance``."""
    return category.replace("_", " ").title()


def format_report(
    month: str,
    entry: MonthEntry,
    summary: Summary,
    score: int,
    comparison: Comparison | None = None,
) -> str:
    """Baut den vollständigen Bericht."""
    lines: list[str] = [
        f"Month: {month}",
        f"Income: {format_money(entry.income)}",
        "",
        "Expenses:",
    ]
    lines.extend(_expense_lines(entry, summary))
    lines.extend(_summary_lines(summary, score))

    if comparison is not None:
        lines.extend(_comparison_lines(comparison))
    else:
        lines.extend(["", "No previous month data to compare."])

    return "\n".join(lines)


def _expense_lines(entry: MonthEntry, summary: Summary) -> list[str]:
    """Eine Zeile je Kategorie, in der Reihenfolge aus der Konfiguration."""
    known = list(CATEGORIES)
    extra = sorted(category for category in entry.expenses if category not in known)

    lines = []
    for category in known + extra:
        value = entry.expenses.get(category, ZERO)
        percentage = summary.percentages.get(category, Decimal("0"))
        lines.append(
            f"  {format_category(category):<20}"
            f"{format_money(value):>12}  ({format_percent(percentage)})"
        )
    return lines


def _summary_lines(summary: Summary, score: int) -> list[str]:
    return [
        "",
        f"Total expenses: {format_money(summary.total_expenses)}",
        f"Remaining:      {format_money(summary.remaining)}",
        f"Savings rate:   {format_percent(summary.savings_rate * HUNDRED)}",
        f"Score:          {score}/100 ({score_label(score)})",
    ]


def _comparison_lines(comparison: Comparison) -> list[str]:
    lines = [
        "",
        "Month-over-month (current minus previous):",
        f"  Income:         {format_money(comparison.income_diff)}",
        f"  Total expenses: {format_money(comparison.total_expenses_diff)}",
        f"  Remaining:      {format_money(comparison.remaining_diff)}",
        f"  Savings rate:   {format_percent(comparison.savings_rate_diff * HUNDRED)}",
    ]

    changes = comparison.biggest_changes()
    if changes:
        lines.append("")
        lines.append("Biggest category changes:")
        for category, value in changes:
            lines.append(f"  {format_category(category):<20}{format_money(value):>12}")
    return lines
