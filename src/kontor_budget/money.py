"""Umgang mit Geldbeträgen.

Jeder Geldwert im Projekt läuft durch dieses Modul. Es ist die einzige
Stelle, die ``Decimal`` erzeugt oder rundet. Warum kein ``float``
verwendet wird, steht im README unter Designentscheidungen.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import TypeAlias

from kontor_budget.config import MONEY_PRECISION
from kontor_budget.errors import ValidationError

#: Sprechender Alias. Ein ``Money`` ist immer ein auf zwei Nachkommastellen
#: quantisierter ``Decimal``.
Money: TypeAlias = Decimal

ZERO: Money = Decimal("0.00")


def to_money(value: object) -> Money:
    """Wandelt einen beliebigen numerischen Wert in einen Geldbetrag um.

    ``float`` wird bewusst über ``str`` konvertiert. ``Decimal(0.1)`` würde
    den Gleitkommafehler übernehmen und ``0.1000000000000000055511151231``
    ergeben, ``Decimal("0.1")`` dagegen exakt ``0.1``.
    """
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, float):
        result = Decimal(str(value))
    elif isinstance(value, (int, str)):
        try:
            result = Decimal(value)
        except InvalidOperation as exc:
            raise ValidationError(f"Not a valid amount: {value!r}") from exc
    else:
        raise ValidationError(f"Unsupported amount type: {type(value).__name__}")

    if not result.is_finite():
        raise ValidationError("Amount must be a finite number")

    return result.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def parse_money(text: str) -> Money:
    """Liest einen Geldbetrag aus einer Benutzereingabe.

    Akzeptiert deutsche und englische Schreibweise. Bei einem Komma im Text
    gilt die deutsche Konvention: Punkt trennt Tausender, Komma trennt
    Dezimalstellen.

        >>> parse_money("1.234,56")
        Decimal('1234.56')
        >>> parse_money("1234.56")
        Decimal('1234.56')
    """
    if not isinstance(text, str):
        raise ValidationError("Amount must be provided as text")

    cleaned = text.strip()
    if not cleaned:
        raise ValidationError("Amount cannot be empty")

    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")

    amount = to_money(cleaned)

    if amount < ZERO:
        raise ValidationError("Amount cannot be negative")

    return amount


def ratio(numerator: Money, denominator: Money) -> Decimal:
    """Teilt zwei Beträge und gibt bei Nenner null ``0`` zurück.

    Vermeidet, dass die Prüfung auf Division durch null an mehreren
    Stellen wiederholt werden muss.
    """
    if denominator == 0:
        return Decimal("0")
    return numerator / denominator
