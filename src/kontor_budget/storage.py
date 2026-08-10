"""Laden und Speichern der Budgetdaten als JSON.

Geldbeträge werden als Strings abgelegt, nicht als JSON-Zahlen. JSON kennt
nur Gleitkommazahlen; ein Umweg über ``float`` würde beim Laden genau die
Rundungsfehler zurückbringen, die ``Decimal`` verhindern soll.
"""

from __future__ import annotations

import json
from pathlib import Path

from kontor_budget.config import DATA_FILE
from kontor_budget.errors import StorageError
from kontor_budget.models import MonthEntry
from kontor_budget.money import to_money

BudgetData = dict[str, MonthEntry]


def load_data(filename: str | Path = DATA_FILE) -> BudgetData:
    """Lädt die Budgetdaten.

    Eine fehlende Datei ist kein Fehler, sondern der erste Programmstart und
    liefert ein leeres Ergebnis. Eine beschädigte Datei ebenfalls, damit ein
    einzelner defekter Eintrag nicht den gesamten Verlauf unbrauchbar macht.
    """
    path = Path(filename)
    if not path.exists():
        return {}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(raw, dict):
        return {}

    data: BudgetData = {}
    for month, payload in raw.items():
        entry = _decode_entry(payload)
        if entry is not None:
            data[month] = entry
    return data


def save_data(data: BudgetData, filename: str | Path = DATA_FILE) -> None:
    """Speichert die Budgetdaten.

    Erst in eine temporäre Datei, dann umbenennen. Bricht der Vorgang ab,
    bleibt die alte Datei unversehrt, statt halb beschrieben zurückzubleiben.
    """
    path = Path(filename)
    payload = {
        month: {
            "income": str(entry.income),
            "expenses": {
                category: str(value) for category, value in entry.expenses.items()
            },
        }
        for month, entry in data.items()
    }

    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise StorageError(f"Could not write {path}") from exc


def _decode_entry(payload: object) -> MonthEntry | None:
    """Baut aus einem gespeicherten Eintrag ein ``MonthEntry``.

    Gibt ``None`` zurück, wenn der Eintrag unbrauchbar ist.
    """
    if not isinstance(payload, dict):
        return None

    raw_expenses = payload.get("expenses", {})
    if not isinstance(raw_expenses, dict):
        raw_expenses = {}

    try:
        return MonthEntry(
            income=to_money(payload.get("income", "0")),
            expenses={
                category: to_money(value) for category, value in raw_expenses.items()
            },
        )
    except (ValueError, TypeError):
        return None
