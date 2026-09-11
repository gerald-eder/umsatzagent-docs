"""Stufe 5: Prompt-Vorlagen je Branche erzeugen.

Die Vorbilder im Netz schreiben einen langen Freitext-Prompt, der Rolle,
Gesprächsablauf, Buchungslogik und Zahlenaussprache in einem Block beschreibt.
Für GoHighLevel ist das falsch: Buchung, Datum, Zahlen und E-Mail-Bestätigung
stecken dort bereits als getestete Module im Systemprompt des Telefon-Agenten,
und wer sie überschreibt, pflegt sie ab dann selbst.

Diese Stufe erzeugt deshalb Vorlagen in der Form, die GoHighLevel erwartet:
Rolle, Aufgabe und Leitplanken für den Chat, ein reiner Personality-Text fürs
Telefon, dazu die Liste der einzuschaltenden Aktionen und das, was in die
Wissensdatenbank gehört statt in den Prompt.

    python3 tools/kb/vorlagen.py
    python3 tools/kb/vorlagen.py --nur "Tiermedizin" --trocken
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
import config, build

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, ".kb-cache")
ZIEL = os.path.join(ROOT, "wissen", "anna-prompt-vorlagen.mdx")
KARTE = os.path.join(CACHE, "vorlagen.json")

# Die Branchen aus ABOUT/icp.md, in denen UmsatzAgent aktive Kunden hat.
BRANCHEN = [
    ("Finanzvermittlung", "chart-line",
     "Anfragen zu Finanzierung, Anlage oder Absicherung. Beratungstermin ist das Ziel."),
    ("Versicherungsmaklerbüro", "shield-halved",
     "Schadensmeldungen, Vertragsfragen, Angebotsanfragen — sehr unterschiedliche Dringlichkeit."),
    ("Coaching", "user-tie",
     "Interessenten aus Social Media und Website, Erstgespräch als Ziel."),
    ("Unternehmensberatung", "briefcase",
     "Erklärungsbedürftige Leistung, längere Entscheidungswege, Qualifizierung zählt."),
    ("Immobilienmaklerbüro", "house",
     "Objektanfragen, Besichtigungswünsche, Verkäufer mit Bewertungsinteresse."),
    ("Fitnessstudio und EMS", "dumbbell",
     "Probetraining, Tarife, Kündigungen. Viel Volumen, kurze Nachrichten."),
    ("Gesundheit und Nahrungsergänzung", "leaf",
     "Produktfragen, Bestellstatus, gesundheitsbezogene Aussagen mit Vorsicht."),
    ("Tierarztpraxis", "paw",
     "Terminwünsche, Notfälle, Medikamentennachfragen. Notfälle haben Vorrang."),
    ("Fintech", "building-columns",
     "Produktfragen, Onboarding-Hürden, regulierte Aussagen."),
]

ANWEISUNG = """Du schreibst eine Prompt-Vorlage für Anna, die KI-Assistentin von UmsatzAgent. UmsatzAgent ist GoHighLevel als deutschsprachiges White-Label; die Vorlage muss deshalb exakt zu dessen Aufbau passen.

WAS DAS SYSTEM BEREITS ERLEDIGT — niemals in die Vorlage schreiben:
Der Telefon-Assistent bringt fertige, getestete Systemprompt-Module mit: Terminbuchung, Datums- und Uhrzeit-Logik, Aussprache von Zahlen und Symbolen, E-Mail-Bestätigung. Beschreibe nichts davon. Wer diese Module überschreibt, muss sie dauerhaft selbst pflegen.

WAS IN DIE WISSENSDATENBANK GEHÖRT — nicht in den Prompt:
Preise, Öffnungszeiten, Adressen, Leistungsbeschreibungen, Produktdetails. Der Prompt verweist nur darauf.

DIE VORLAGE HAT GENAU DIESE VIER TEILE:

1. "chat" — der Prompt für den Chat-Assistenten (Bot Goals). Aufgebaut als drei Abschnitte mit den Überschriften "## Rolle", "## Aufgabe", "## Leitplanken". Die Leitplanken sind Wenn-dann-Sätze. Höchstens 220 Wörter insgesamt. Platzhalter in eckigen Klammern, zum Beispiel [Firma], [Notfallnummer].

2. "telefon" — nur der Personality-Text für den Telefon-Assistenten. Höchstens 90 Wörter. Beschreibt Auftreten, Sprechtempo, Umgang mit Unsicherheit. Keine Buchungs-, Datums- oder Zahlenregeln.

3. "aktionen" — Liste der Bot-Actions, die für diese Branche eingeschaltet gehören, je mit einem Halbsatz warum. Wähle aus: Add Contact Info, Appointment Booking, Transfer, Human Handover, Workflow auslösen.

4. "wissensdatenbank" — Liste der Inhalte, die dieser Betrieb hinterlegen sollte, damit Anna nicht rät. Vier bis sechs Stichpunkte.

SPRACHE:
Durchgehend Deutsch, "du" gegenüber dem Leser. Native Umlaute. Sachlich, keine Werbesprache. Anna selbst siezt oder duzt je nach Gegenüber — das steht als Regel im Prompt.

Antworte ausschließlich als JSON-Objekt mit genau diesen Schlüsseln:
{"chat": "...", "telefon": "...", "aktionen": [{"name": "...", "warum": "..."}], "wissensdatenbank": ["...", "..."]}

BRANCHE: {branche}
TYPISCHE ANLIEGEN: {kontext}"""


def erzeuge(branche, kontext, key, modell):
    frage = ANWEISUNG.replace("{branche}", branche).replace("{kontext}", kontext)
    antwort = build.uebersetze(branche, frage, key, modell) or ""
    m = re.search(r"\{.*\}", antwort, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nur", help="nur diese Branche")
    ap.add_argument("--trocken", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    karte = json.load(open(KARTE)) if os.path.exists(KARTE) and not a.force else {}
    key = build.api_key()

    for name, icon, kontext in BRANCHEN:
        if a.nur and a.nur.lower() not in name.lower():
            continue
        if name in karte:
            print(f"  cache  {name}")
            continue
        v = erzeuge(name, kontext, key, config.MODELL)
        if not v:
            print(f"  FEHLER {name}")
            continue
        karte[name] = v
        print(f"  neu    {name}")
        json.dump(karte, open(KARTE, "w"), ensure_ascii=False, indent=1)

    if a.trocken:
        for n, v in karte.items():
            print(f"\n=== {n} ===\n{v['chat'][:400]}")
        return

    bloecke = []
    for name, icon, kontext in BRANCHEN:
        v = karte.get(name)
        if not v:
            continue
        aktionen = "\n".join(
            f'| {x.get("name","")} | {x.get("warum","")} |' for x in v.get("aktionen", []))
        wissen = "\n".join(f"- {x}" for x in v.get("wissensdatenbank", []))
        bloecke.append(
            f'<Accordion title="{name}" icon="{icon}">\n\n'
            f"**Für den Chat** — einfügen unter AI-Assistenten → Conversation AI → "
            f"Assistent → Bot Goals:\n\n"
            f"```text {name} — Chat\n{v['chat'].strip()}\n```\n\n"
            f"**Fürs Telefon** — nur das Modul Personality unter AI-Assistenten → "
            f"Voice AI → Agent Goals → View System Prompt:\n\n"
            f"```text {name} — Telefon (Personality)\n{v['telefon'].strip()}\n```\n\n"
            f"**Diese Aktionen einschalten:**\n\n"
            f"| Aktion | Wofür |\n|---|---|\n{aktionen}\n\n"
            f"**Das gehört in die Wissensdatenbank, nicht in den Prompt:**\n\n{wissen}\n\n"
            f"</Accordion>"
        )

    seite = (
        '---\ntitle: "Prompt-Vorlagen nach Branche"\n'
        'description: "Fertige Prompts für Anna — zugeschnitten auf neun Branchen, '
        'in der Form, die UmsatzAgent erwartet."\n---\n\n'
        "Wähl deine Branche, kopier den Prompt, ersetz die Platzhalter in eckigen\n"
        "Klammern. Jede Vorlage hat zwei Teile, weil Chat und Telefon getrennt\n"
        "eingerichtet werden.\n\n"
        "<Warning>\n"
        "  Die Vorlagen beschreiben bewusst **keine** Buchungslogik, Datumsregeln\n"
        "  oder Zahlenaussprache. Das steckt am Telefon bereits als getestetes Modul\n"
        "  im Systemprompt. Wer es überschreibt, pflegt es ab dann selbst. Warum das\n"
        "  so ist: [Anna einen guten Prompt geben](/wissen/anna-prompt-schreiben).\n"
        "</Warning>\n\n"
        "<AccordionGroup>\n\n" + "\n\n".join(bloecke) + "\n\n</AccordionGroup>\n\n"
        "## Deine Branche ist nicht dabei?\n\n"
        "Nimm die ähnlichste als Ausgangspunkt — der Aufbau ist überall gleich, nur\n"
        "die Anliegen unterscheiden sich. Oder bring sie in den Weekly Call mit,\n"
        "dann bauen wir sie gemeinsam.\n\n"
        "<Columns cols={2}>\n"
        '  <Card title="Weekly Q&A-Call" icon="calendar-days" '
        'href="https://click.umsatzagent.com/widget/bookings/weekly-q-a-call">\n'
        "    Jeden Dienstag 14:00.\n  </Card>\n"
        '  <Card title="So funktionieren Prompts" icon="lightbulb" '
        'href="/wissen/anna-prompt-schreiben">\n'
        "    Der Aufbau dahinter, in fünf Minuten.\n  </Card>\n"
        "</Columns>\n"
    )
    open(ZIEL, "w").write(seite)
    print(f"\n{len(bloecke)} Branchen geschrieben: {os.path.relpath(ZIEL, ROOT)}")


if __name__ == "__main__":
    main()
