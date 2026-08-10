"""Datenmodelle der Anwendung.

Alle Modelle sind ``frozen``: einmal erzeugt, werden sie nicht mehr
verändert. Wer einen anderen Wert braucht, erzeugt ein neues Objekt.
Dasselbe Prinzip gilt in echten Buchhaltungssystemen für gebuchte
Vorgänge, und es macht Berechnungen nachvollziehbar, weil kein Aufrufer
die Eingabedaten unter der Hand ändern kann.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType

from kontor_budget.money import ZERO, Money, to_money


def _freeze(expenses: Mapping[str, object]) -> Mapping[str, Money]:
    """Normalisiert Ausgaben zu Geldbeträgen und schützt sie vor Änderung."""
    return MappingProxyType(
        {category: to_money(value) for category, value in expenses.items()}
    )


@dataclass(frozen=True, slots=True)
class MonthEntry:
    """Einkommen und Ausgaben eines einzelnen Monats."""

    income: Money
    expenses: Mapping[str, Money] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Bei frozen dataclasses ist direkte Zuweisung gesperrt, deshalb
        # der Umweg über object.__setattr__.
        object.__setattr__(self, "income", to_money(self.income))
        object.__setattr__(self, "expenses", _freeze(self.expenses))

    @property
    def total_expenses(self) -> Money:
        """Summe aller Ausgaben des Monats."""
        return sum(self.expenses.values(), start=ZERO)


@dataclass(frozen=True, slots=True)
class Summary:
    """Ausgewertetes Ergebnis eines Monats."""

    total_expenses: Money
    remaining: Money
    percentages: Mapping[str, Decimal]
    savings_rate: Decimal


@dataclass(frozen=True, slots=True)
class Comparison:
    """Differenzen zwischen zwei Monaten, jeweils aktuell minus vorher."""

    income_diff: Money
    total_expenses_diff: Money
    remaining_diff: Money
    savings_rate_diff: Decimal
    category_diff: Mapping[str, Money]

    def biggest_changes(self, limit: int = 2) -> list[tuple[str, Money]]:
        """Gibt die Kategorien mit der größten absoluten Änderung zurück."""
        ordered = sorted(
            self.category_diff.items(),
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        return ordered[:limit]
