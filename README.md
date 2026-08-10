# Kontor Budget

[![tests](https://github.com/USERNAME/kontor-budget/actions/workflows/tests.yml/badge.svg)](https://github.com/USERNAME/kontor-budget/actions/workflows/tests.yml)

Ein Kommandozeilenwerkzeug zur Verwaltung monatlicher Einnahmen und Ausgaben.
Es berechnet die Sparquote und einen Score und vergleicht den aktuellen Monat
mit dem Vormonat.

Teil der **Kontor**-Reihe, in der ich mich damit beschäftige, wie Geld erfasst
und bewegt wird. Dieses Projekt ist die persönliche Sicht auf das Thema;
[kontor-ledger](https://github.com/USERNAME/kontor-ledger) setzt dieselben
Fragen mit doppelter Buchführung in Java um.

## Features

- Erfassung von Einkommen und Ausgaben in konfigurierbaren Kategorien
- Sparquote und prozentualer Anteil jeder Kategorie am Einkommen
- Score von 0 bis 100, gemessen an einer Zielsparquote von 30 Prozent
- Monatsvergleich inklusive der größten Kategorieveränderungen
- Eingabevalidierung für deutsche und englische Zahlenschreibweise
- Persistenz als JSON, Beträge verlustfrei gespeichert

## Installation

Python 3.11 oder neuer.

```bash
git clone https://github.com/USERNAME/kontor-budget.git
cd kontor-budget
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Verwendung

```bash
# Neuen Monat erfassen
kontor-budget

# Gespeicherten Monat anzeigen
kontor-budget --show 2026-07

# Andere Datendatei verwenden
kontor-budget --file haushalt.json
```

Zum Ausprobieren kann `data.example.json` nach `data.json` kopiert werden.

### Beispielausgabe

```
Month: 2026-08
Income: 2,100.00

Expenses:
  Rent                      450.00  (21.4%)
  Food                      300.00  (14.3%)
  Investment                250.00  (11.9%)

Total expenses: 1,260.00
Remaining:      840.00
Savings rate:   40.0%
Score:          100/100 (Excellent)

Month-over-month (current minus previous):
  Income:         150.00
  Total expenses: 35.00
```

## Tests

```bash
pytest          # 67 Tests
ruff check .    # Linting
```

## Projektstruktur

```
src/kontor_budget/
  config.py        Kategorien, Zielsparquote, Genauigkeit
  errors.py        Eigene Fehlertypen
  money.py         Einzige Stelle, die Decimal erzeugt und rundet
  models.py        Unveränderliche Datenmodelle
  validation.py    Prüfung von Monatsangaben
  calculations.py  Auswertung und Monatsvergleich, rein funktional
  storage.py       Laden und Speichern
  report.py        Formatierung der Ausgabe
  cli.py           Benutzerinteraktion, Einstiegspunkt
tests/
```

## Designentscheidungen

### `Decimal` statt `float` für Geldbeträge

Gleitkommazahlen können Dezimalbrüche nicht exakt darstellen. In Python ergibt
`0.1 + 0.2` den Wert `0.30000000000000004`. Bei einem einzelnen Monat fällt das
nicht auf, über viele Buchungen summieren sich diese Abweichungen jedoch und
Salden stimmen nicht mehr. Aus demselben Grund verwendet kein reales
Finanzsystem Gleitkommazahlen für Geld.

`money.py` ist die einzige Stelle, die `Decimal` erzeugt. Beträge werden bei der
Eingabe auf zwei Nachkommastellen quantisiert (`ROUND_HALF_UP`). `float`-Werte
laufen bewusst über `str`, weil `Decimal(0.1)` den binären Fehler übernehmen
würde, `Decimal("0.1")` dagegen nicht.

### Beträge werden als Strings gespeichert

JSON kennt nur Gleitkommazahlen. Würde man `Decimal` direkt serialisieren, ginge
die Genauigkeit beim Laden wieder verloren. Der Umweg über Strings hält die
Werte exakt — nachgewiesen durch einen Roundtrip-Test.

### Unveränderliche Modelle

`MonthEntry`, `Summary` und `Comparison` sind `frozen` dataclasses und geben
ihre Ausgaben als `MappingProxyType` heraus. Ein einmal erfasster Monat wird
nicht nachträglich verändert; wer einen anderen Wert braucht, erzeugt ein neues
Objekt. Dasselbe Prinzip gilt in Buchhaltungssystemen für gebuchte Vorgänge:
eine fehlerhafte Buchung wird nicht korrigiert, sondern gegengebucht.

### Trennung nach Verantwortung

Berechnung, Validierung, Formatierung und Persistenz sind getrennte Module. Nur
`cli.py` verwendet `input` und `print`. Dadurch ist die gesamte Logik ohne
Datei- oder Konsolenzugriff testbar, und die Ausgabe lässt sich ändern, ohne die
Berechnung anzufassen.

### Atomares Schreiben

`save_data` schreibt zuerst in eine temporäre Datei und benennt sie anschließend
um. Bricht der Vorgang ab, bleibt die alte Datei unversehrt, statt halb
beschrieben zurückzubleiben.

### Defensives Laden

Eine fehlende Datei ist kein Fehler, sondern der erste Programmstart. Ein
einzelner beschädigter Eintrag führt nicht dazu, dass der gesamte Verlauf
verloren geht — er wird übersprungen.

### `data.json` steht in `.gitignore`

Die Datei enthält echte persönliche Finanzdaten. Versioniert wird
ausschließlich `data.example.json` mit Beispielwerten.

## Nächste Schritte

- REST-API mit FastAPI, damit die Logik nicht nur über die Konsole nutzbar ist
- PostgreSQL statt JSON
- Mehrere Währungen

## Lizenz

MIT
