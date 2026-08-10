"""Validierung von Monatsangaben im Format ``YYYY-MM``."""

from __future__ import annotations

from kontor_budget.errors import ValidationError

MIN_YEAR = 1900
MAX_YEAR = 3000


def validate_month(month: str) -> str:
    """Prüft eine Monatsangabe und gibt sie normalisiert zurück.

    >>> validate_month("  2026-8  ")
    Traceback (most recent call last):
    ...
    kontor_budget.errors.ValidationError: Month must be 2 digits
    >>> validate_month("2026-08")
    '2026-08'
    """
    if not isinstance(month, str):
        raise ValidationError("Month must be a string in format YYYY-MM")

    parts = month.strip().split("-")
    if len(parts) != 2:
        raise ValidationError("Month must be in format YYYY-MM")

    year_str, month_str = parts
    if len(year_str) != 4 or not year_str.isdigit():
        raise ValidationError("Year must be 4 digits")
    if len(month_str) != 2 or not month_str.isdigit():
        raise ValidationError("Month must be 2 digits")

    year = int(year_str)
    month_number = int(month_str)

    if not MIN_YEAR <= year <= MAX_YEAR:
        raise ValidationError(f"Year must be between {MIN_YEAR} and {MAX_YEAR}")
    if not 1 <= month_number <= 12:
        raise ValidationError("Month must be between 01 and 12")

    return f"{year:04d}-{month_number:02d}"


def previous_month(month: str) -> str:
    """Gibt den Vormonat zurück und behandelt den Jahreswechsel.

    >>> previous_month("2026-01")
    '2025-12'
    """
    normalized = validate_month(month)
    year = int(normalized[:4])
    month_number = int(normalized[5:7])

    if month_number == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{month_number - 1:02d}"
