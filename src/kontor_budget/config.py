"""Zentrale Konfiguration.

Alle Werte, die das Verhalten der Anwendung steuern, stehen hier an einer
Stelle. Kein anderes Modul definiert eigene Konstanten.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Final

#: Standarddateiname für die gespeicherten Budgetdaten.
DATA_FILE: Final[str] = "data.json"

#: Ausgabekategorien in der Reihenfolge, in der sie abgefragt und
#: ausgegeben werden.
CATEGORIES: Final[tuple[str, ...]] = (
    "rent",
    "food",
    "investment",
    "health_insurance",
    "gas",
    "installments",
)

#: Zielsparquote. 30 Prozent des Einkommens entsprechen einem Score von 100.
TARGET_SAVINGS_RATE: Final[Decimal] = Decimal("0.30")

#: Genauigkeit aller Geldbeträge: zwei Nachkommastellen.
MONEY_PRECISION: Final[Decimal] = Decimal("0.01")

#: Untergrenzen der Score-Labels.
SCORE_THRESHOLDS: Final[tuple[tuple[int, str], ...]] = (
    (80, "Excellent"),
    (60, "Good"),
    (40, "OK"),
    (0, "Weak"),
)
