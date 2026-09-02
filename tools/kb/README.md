# Wissensdatenbank-Übernahme

Holt die Hilfe-Artikel der Plattform-Quelle, übersetzt sie ins Deutsche,
schreibt sie auf UmsatzAgent um und legt sie als Mintlify-Seiten ab.

## Ablauf

```bash
python3 tools/kb/pull.py      # Quelle -> .kb-cache/  (nur was fehlt)
python3 tools/kb/build.py     # übersetzen -> wissen/*.mdx + images/wissen/
python3 tools/kb/nav.py       # Navigation -> docs.json
```

Jede Stufe ist wiederholbar und überspringt, was schon erledigt ist. Ein
zweiter Lauf kostet also nichts und holt nur Neues nach.

`pull.py` läuft bei 764 Artikeln ins Rate-Limit der Quelle und holt pro Lauf
nur einen Teil. Das ist kein Fehler — einfach zwei- bis dreimal starten, bis
`Fertig: 0 geholt` steht.

## Nützliche Schalter

```bash
python3 tools/kb/build.py --ordner "Quick Start Guides"   # nur ein Ordner
python3 tools/kb/build.py --limit 5 --trocken             # Probe, schreibt nichts
python3 tools/kb/build.py --force                         # Übersetzung erneuern
python3 tools/kb/build.py --parallel 8                    # schneller
```

## Was wo eingestellt wird

Alles in `config.py`:

- `GLOSSAR` — englischer Oberflächenbegriff → deutsche Entsprechung. Der
  wichtigste Hebel für die Qualität. Stimmt ein Begriff nicht mit der App
  überein, hier korrigieren und `build.py --force` laufen lassen.
- `MARKEN` — Fremdmarken und ihre Ersetzung. Wird nach der Übersetzung
  stumpf angewendet, unabhängig davon, was das Modell getan hat.
- `VERBOTEN` — Begriffe, die im Ergebnis nicht vorkommen dürfen. Jeder
  Treffer wird am Ende des Laufs gemeldet.
- `THEMEN` — Bündelung der 41 Quell-Kategorien zu Seitenleisten-Gruppen.
- `AUSGESCHLOSSEN` — Kategorien, die gar nicht übernommen werden.

Die erzeugten `.mdx`-Dateien werden bei jedem Lauf überschrieben. Wer eine
Übersetzung dauerhaft korrigieren will, ändert das Glossar — nicht die Datei.

## Grenzen

- **Videos.** 23 Artikel binden Videos der Quelle ein. Die zeigen deren Marke
  im Bild, das lässt sich nicht übersetzen. Sie müssen nachgedreht oder
  entfernt werden. Liste nach dem Lauf in `.kb-cache/nacharbeit.json`.
- **Agentur-Inhalte.** Rund 144 Artikel sprechen über Agentur-Konten,
  Unterkonten, Snapshots oder Reseller-Funktionen. Sie verraten, dass hinter
  der Oberfläche eine Reseller-Plattform steckt. Vor der Veröffentlichung
  prüfen, besser ganz ausschließen.
- **Bilder.** Rund 3.500 Screenshots, zusammen etwa 640 MB. Das gehört nicht
  ins Git-Repo — für den Vollausbau auf einen Objektspeicher auslagern und
  `config.BILDER` auf dessen URL zeigen lassen.
- **Aktualität.** Die Quelle ändert ihre Artikel laufend. Ein Lauf ist eine
  Momentaufnahme; `pull.py` und `build.py` regelmäßig wiederholen.
