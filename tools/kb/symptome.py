"""Stufe 4: Eine Seite, die nach Symptom sortiert statt nach Funktion.

Die Quelle ordnet nach Bauteil: E-Mail, Kalender, Workflow. Wer ein Problem
hat, sucht aber nicht nach dem Bauteil, sondern nach dem Symptom — "meine
Mails kommen nicht an". Diese Stufe legt eine Brücke: Sie ordnet vorhandene
Artikel den Symptomen zu und schreibt daraus eine Einstiegsseite. Es entstehen
keine neuen Inhalte, nur ein zweiter Weg zu denselben.

    python3 tools/kb/symptome.py            # zuordnen und Seite schreiben
    python3 tools/kb/symptome.py --trocken  # nur zeigen
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
import config, build

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, ".kb-cache")
ZIEL = os.path.join(ROOT, "wissen", "etwas-funktioniert-nicht.mdx")
KARTE = os.path.join(CACHE, "symptome.json")

# In der Sprache des Kunden, nicht in der des Produkts.
SYMPTOME = [
    ("Meine E-Mails kommen nicht an", "envelope-open-text",
     "Zustellprobleme, Spam-Ordner, Authentifizierung, Sendelimits."),
    ("WhatsApp lässt sich nicht verbinden", "whatsapp",
     "Verifizierung, gesperrte Konten, abgelehnte Anzeigenamen."),
    ("Anrufe kommen nicht durch", "phone-slash",
     "Weiterleitung, Telefonnummern, Sprachanrufe."),
    ("Termine werden nicht gebucht", "calendar-xmark",
     "Kalender-Verbindung, Verfügbarkeiten, Buchungsstrecke."),
    ("Eine Integration verbindet sich nicht", "plug-circle-xmark",
     "Facebook, Instagram, Google, Outlook und andere Konten."),
    ("Domain oder Website macht Probleme", "globe",
     "DNS, Verifizierung, Veröffentlichung, Tracking."),
    ("Eine Zahlung ist fehlgeschlagen", "credit-card",
     "Abbuchungen, Wiederholungsversuche, Abos, Rückerstattungen."),
    ("Der Assistent antwortet falsch", "robot",
     "Prompts, Wissensdatenbank, Ziele, Assistenten-Aktionen."),
    ("Kontakte oder Daten fehlen", "file-import",
     "Import, Felder, Duplikate, Listen."),
]

ANWEISUNG = """Du ordnest Hilfe-Artikel einer deutschsprachigen Marketing- und Vertriebssoftware den Problemen zu, mit denen Kunden im Support ankommen.

Unten stehen nummerierte Artikeltitel und darunter die Symptome. Ordne jedem Symptom die Artikel zu, die einem Kunden mit genau diesem Problem tatsächlich weiterhelfen.

Regeln:
- Höchstens sechs Artikel je Symptom, sortiert vom wahrscheinlichsten zum selteneren Fall.
- Nur zuordnen, was wirklich hilft. Lieber drei treffende als sechs halbgare.
- Ein Artikel darf bei mehreren Symptomen stehen, wenn er dort jeweils passt.
- Ein Artikel, der zu keinem Symptom passt, bleibt weg. Das ist der Normalfall — die meisten Artikel beschreiben Einrichtung, nicht Fehler.

Antworte ausschließlich als JSON-Objekt: die Symptomnummer als Schlüssel, eine Liste der Artikelnummern als Wert.
Beispiel: {"1": [12, 340, 7], "2": [88]}

SYMPTOME:
{symptome}

ARTIKEL:
{artikel}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trocken", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    artikel = []
    for f in sorted(os.listdir(os.path.join(CACHE, "de"))):
        b = json.load(open(os.path.join(CACHE, "de", f)))
        if b.get("pfad") and os.path.exists(os.path.join(ROOT, b["pfad"] + ".mdx")):
            artikel.append((b["titel"], b["pfad"]))

    if not artikel:
        sys.exit("Keine gebauten Artikel gefunden.")

    if os.path.exists(KARTE) and not a.force:
        karte = json.load(open(KARTE))
        print(f"Zuordnung aus dem Cache ({KARTE})")
    else:
        frage = ANWEISUNG.replace(
            "{symptome}",
            "\n".join(f"{i+1}. {name} — {hint}" for i, (name, _, hint) in enumerate(SYMPTOME)),
        ).replace(
            "{artikel}",
            "\n".join(f"{i+1}. {t}" for i, (t, _) in enumerate(artikel)),
        )
        antwort = build.uebersetze("Symptome", frage, build.api_key(), config.MODELL) or ""
        m = re.search(r"\{.*\}", antwort, re.S)
        if not m:
            sys.exit("Modell lieferte kein JSON.")
        karte = json.loads(m.group(0))
        json.dump(karte, open(KARTE, "w"), ensure_ascii=False, indent=1)
        print(f"Zuordnung erzeugt und gespeichert")

    zeilen = []
    gesamt = 0
    for i, (name, icon, hint) in enumerate(SYMPTOME, 1):
        nummern = [n for n in karte.get(str(i), []) if isinstance(n, int) and 1 <= n <= len(artikel)]
        if not nummern:
            print(f"  ⚠ ohne Artikel: {name}")
            continue
        gesamt += len(nummern)
        print(f"  {len(nummern):>2}  {name}")
        eintraege = "\n".join(
            f'  <Card title="{artikel[n-1][0].replace(chr(34), chr(39))}" '
            f'href="/{artikel[n-1][1]}" horizontal />'
            for n in nummern
        )
        zeilen.append(
            f'<Accordion title="{name}" icon="{icon}">\n'
            f"  {hint}\n\n"
            f"{eintraege}\n"
            f"</Accordion>"
        )

    seite = (
        '---\ntitle: "Etwas funktioniert nicht"\n'
        'description: "Such nach dem, was du siehst — nicht nach dem Bauteil, '
        'in dem es steckt."\n---\n\n'
        "Die Anleitungen sind nach Funktion sortiert: E-Mail, Kalender, Telefonie.\n"
        "Wenn etwas klemmt, weiß man aber selten, welches Bauteil schuld ist —\n"
        "man sieht nur, was nicht passiert. Deshalb hier derselbe Bestand,\n"
        "sortiert nach dem, was du beobachtest.\n\n"
        "<AccordionGroup>\n\n" + "\n\n".join(zeilen) + "\n\n</AccordionGroup>\n\n"
        "## Nichts dabei?\n\n"
        "<Columns cols={2}>\n"
        '  <Card title="Weekly Q&A-Call" icon="calendar-days" '
        'href="https://click.umsatzagent.com/widget/bookings/weekly-q-a-call">\n'
        "    Jeden Dienstag 14:00. Bring die Frage mit.\n"
        "  </Card>\n"
        '  <Card title="1:1 Support-Call" icon="headset" '
        'href="https://click.umsatzagent.com/widget/bookings/umsatzagent-support">\n'
        "    25 Minuten, Mo–Fr ab 15:00.\n"
        "  </Card>\n"
        "</Columns>\n"
    )

    print(f"\n{gesamt} Verweise auf {len(set(n for v in karte.values() for n in v))} Artikel")

    if a.trocken:
        print("Trockenlauf — nichts geschrieben.")
        return

    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    open(ZIEL, "w").write(seite)
    print(f"geschrieben: {os.path.relpath(ZIEL, ROOT)}")
    print("Danach tools/kb/nav.py laufen lassen, damit die Seite in der Navigation steht.")


if __name__ == "__main__":
    main()
