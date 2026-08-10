"""Fehlertypen der Anwendung.

Eigene Ausnahmen statt roher ``ValueError`` machen im Aufrufer sichtbar,
woher ein Fehler stammt. ``ValidationError`` erbt zusätzlich von
``ValueError``, damit bestehender Code, der auf ``ValueError`` prüft,
weiterhin funktioniert.
"""

from __future__ import annotations


class BudgetError(Exception):
    """Basisklasse aller Fehler dieser Anwendung."""


class ValidationError(BudgetError, ValueError):
    """Eine Benutzereingabe ist ungültig."""


class StorageError(BudgetError):
    """Die Datendatei konnte nicht gelesen oder geschrieben werden."""
