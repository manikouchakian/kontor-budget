"""Kommandozeilen-Oberfläche.

Die einzige Stelle im Projekt, die ``input`` und ``print`` verwendet. Alles
darunter bleibt dadurch ohne Konsolenzugriff testbar.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kontor_budget.calculations import calculate_score, calculate_summary, compare_months
from kontor_budget.config import CATEGORIES, DATA_FILE
from kontor_budget.errors import BudgetError, ValidationError
from kontor_budget.models import MonthEntry
from kontor_budget.money import Money, parse_money
from kontor_budget.report import format_category, format_report
from kontor_budget.storage import load_data, save_data
from kontor_budget.validation import previous_month, validate_month


def prompt_month() -> str:
    """Fragt so lange nach einem Monat, bis die Eingabe gültig ist."""
    while True:
        try:
            return validate_month(input("Month (YYYY-MM): "))
        except ValidationError as error:
            print(f"  {error}")


def prompt_money(label: str) -> Money:
    """Fragt so lange nach einem Betrag, bis die Eingabe gültig ist."""
    while True:
        try:
            return parse_money(input(f"{label}: "))
        except ValidationError as error:
            print(f"  {error}")


def collect_entry() -> tuple[str, MonthEntry]:
    """Sammelt einen kompletten Monat über die Konsole ein."""
    month = prompt_month()
    income = prompt_money("Income")
    expenses = {
        category: prompt_money(f"  {format_category(category)}")
        for category in CATEGORIES
    }
    return month, MonthEntry(income=income, expenses=expenses)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kontor-budget",
        description="Track monthly income and expenses, savings rate and score.",
    )
    parser.add_argument(
        "--file",
        default=DATA_FILE,
        type=Path,
        help=f"path to the data file (default: {DATA_FILE})",
    )
    parser.add_argument(
        "--show",
        metavar="YYYY-MM",
        help="print a stored month instead of entering a new one",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    """Einstiegspunkt. Gibt den Exit-Code zurück."""
    args = build_parser().parse_args(argv)

    print("Kontor Budget")
    print("-" * 40)

    data = load_data(args.file)

    if args.show:
        month = validate_month(args.show)
        entry = data.get(month)
        if entry is None:
            print(f"No data stored for {month}.")
            return 1
    else:
        month, entry = collect_entry()
        data[month] = entry
        save_data(data, args.file)

    summary = calculate_summary(entry)
    score = calculate_score(entry.income, summary.remaining)

    comparison = None
    earlier = data.get(previous_month(month))
    if earlier is not None:
        comparison = compare_months(entry, earlier)

    print()
    print(format_report(month, entry, summary, score, comparison))
    return 0


def main() -> None:
    """Wrapper, der Fehler in eine lesbare Meldung übersetzt."""
    try:
        sys.exit(run())
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    except BudgetError as error:
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
