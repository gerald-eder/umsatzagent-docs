"""Stufe 0: Die Artikel der Quelle nach Relevanz einstufen.

Die Quelle schreibt für alle: Endkunden, Agenturen, Reseller, US-Markt. Das
Help Center richtet sich aber nur an zwei Rollen — Konto-Admins und
Vertriebsmitarbeiter im DACH-Raum. Diese Stufe entscheidet, was übernommen
wird, damit build.py nicht 758 Artikel übersetzt, von denen die Hälfte
niemanden hier betrifft.

    python3 tools/kb/auswahl.py            # einstufen (Ergebnis wird gecacht)
    python3 tools/kb/auswahl.py --bericht  # nur Ergebnis anzeigen
"""
import argparse, html, json, os, re, sys
import concurrent.futures as cf

sys.path.insert(0, os.path.dirname(__file__))
import config, build

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, ".kb-cache")
ZIEL = os.path.join(CACHE, "auswahl.json")

ANWEISUNG = """Du sortierst Hilfe-Artikel für das Help Center von UmsatzAgent vor.

UmsatzAgent ist eine deutschsprachige Marketing- und Vertriebssoftware für kleine und mittlere Unternehmen im DACH-Raum. Das Help Center hat genau zwei Zielgruppen:
- ADMIN: die Person, die das Konto einrichtet und verwaltet (Inhaber, Administrator).
- NUTZER: Vertriebs- und Servicemitarbeiter, die täglich damit arbeiten.

Stufe jeden Artikel in genau eine Klasse ein:

- "kern": Onboarding, Konto-Einrichtung, tägliche Arbeit, häufige Fragen und typische Probleme. Das, wonach Admins und Vertriebsmitarbeiter wirklich suchen.
- "rand": fachlich korrekt und im Prinzip nutzbar, aber Spezialfall oder Randfunktion. Später, nicht zuerst.
- "raus": trifft auf mindestens einen Ausschlussgrund zu.

Ausschlussgründe für "raus":
- Richtet sich an Agenturen, Reseller oder Wiederverkäufer statt an Endkunden.
- Behandelt Agentur-Konten, Unterkonten, SaaS-Modus, Snapshots, Rebilling oder White-Label-Einrichtung.
- Betrifft nur die USA oder Kanada: A2P 10DLC, US-Mobilfunkanbieter, US-Steuerrecht, US-Telefonvorschriften.
- Bewirbt einen fremden Marktplatz, ein Partnerprogramm oder eine fremde Preisliste.
- Reine Fehlercode-Nachschlagewerke ohne Handlungsanleitung.

Wichtig für den DACH-Raum und daher eher "kern": WhatsApp, E-Mail-Zustellbarkeit, DSGVO und Datenschutz, Kalender und Termine, Rechnungen, Telefonie in Europa.

Antworte als JSON-Array, ein Objekt je Artikel, gleiche Reihenfolge wie die Eingabe:
[{"n": 1, "klasse": "kern", "rolle": "admin", "grund": "kurz"}]

"rolle" ist "admin", "nutzer" oder "beide". "grund" sind höchstens acht Wörter. Kein weiterer Text, nur das JSON-Array."""


def haeppchen(arts, groesse=25):
    for i in range(0, len(arts), groesse):
        yield arts[i:i + groesse]


def einstufen(gruppe, key, modell):
    zeilen = []
    for i, a in enumerate(gruppe, 1):
        txt = re.sub(r"<[^>]+>", " ", a["html"])
        txt = re.sub(r"\s+", " ", html.unescape(txt)).strip()
        zeilen.append(f'{i}. [{a["ordner"]}] {a["titel_en"]}\n   {txt[:260]}')
    frage = ANWEISUNG + "\n\n" + "\n\n".join(zeilen)
    antwort = build.uebersetze("Einstufung", frage, key, modell) or ""
    m = re.search(r"\[.*\]", antwort, re.S)
    if not m:
        return []
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bericht", action="store_true")
    ap.add_argument("--modell", default=config.MODELL)
    ap.add_argument("--parallel", type=int, default=6)
    a = ap.parse_args()

    struct = json.load(open(os.path.join(CACHE, "struktur.json")))
    heimat, kat_von_ordner = {}, {}
    ordner_name = {}
    for u, k in struct.items():
        if k["art"] == "ordner":
            m = re.search(r"folders/(\d+)", u)
            if m:
                ordner_name[m.group(1)] = html.unescape(k["name"] or "")
            for aid in k["artikel"]:
                heimat[aid] = html.unescape(k["name"] or "")
    for u, k in struct.items():
        if k["art"] == "kategorie":
            for fid in k["ordner"]:
                kat_von_ordner[ordner_name.get(fid, "")] = html.unescape(k["name"] or "")

    arts = []
    for f in sorted(os.listdir(os.path.join(CACHE, "articles"))):
        r = json.load(open(os.path.join(CACHE, "articles", f)))
        r["ordner"] = heimat.get(r["id"], "Sonstiges")
        r["kategorie"] = kat_von_ordner.get(r["ordner"], "Sonstiges")
        arts.append(r)

    ergebnis = json.load(open(ZIEL)) if os.path.exists(ZIEL) else {}

    if not a.bericht:
        offen = [x for x in arts if x["id"] not in ergebnis]
        print(f"{len(offen)} von {len(arts)} Artikeln noch einzustufen")
        gruppen = list(haeppchen(offen))
        key = build.api_key()

        def lauf(g):
            return g, einstufen(g, key, a.modell)

        with cf.ThreadPoolExecutor(max_workers=a.parallel) as ex:
            for i, (g, urteile) in enumerate(ex.map(lauf, gruppen), 1):
                for u in urteile:
                    n = u.get("n")
                    if isinstance(n, int) and 1 <= n <= len(g):
                        art = g[n - 1]
                        ergebnis[art["id"]] = {
                            "klasse": u.get("klasse", "rand"),
                            "rolle": u.get("rolle", "beide"),
                            "grund": u.get("grund", ""),
                            "titel": art["titel_en"],
                            "ordner": art["ordner"],
                            "kategorie": art["kategorie"],
                        }
                print(f"  Häppchen {i}/{len(gruppen)} — {len(ergebnis)} eingestuft")
                json.dump(ergebnis, open(ZIEL, "w"), ensure_ascii=False, indent=1)

    # --- Bericht ----------------------------------------------------------
    if not ergebnis:
        sys.exit("Noch nichts eingestuft.")

    zaehl = {"kern": 0, "rand": 0, "raus": 0}
    nach_kat = {}
    for v in ergebnis.values():
        zaehl[v["klasse"]] = zaehl.get(v["klasse"], 0) + 1
        nach_kat.setdefault(v["kategorie"], {"kern": 0, "rand": 0, "raus": 0})
        nach_kat[v["kategorie"]][v["klasse"]] = nach_kat[v["kategorie"]].get(v["klasse"], 0) + 1

    gesamt = sum(zaehl.values())
    print(f"\n{gesamt} Artikel eingestuft")
    print(f"  kern {zaehl['kern']}   rand {zaehl['rand']}   raus {zaehl['raus']}")

    print(f"\n{'kern':>5} {'rand':>5} {'raus':>5}  Kategorie")
    for k, v in sorted(nach_kat.items(), key=lambda x: -x[1]["kern"]):
        print(f"{v['kern']:>5} {v['rand']:>5} {v['raus']:>5}  {k}")

    gruende = {}
    for v in ergebnis.values():
        if v["klasse"] == "raus":
            gruende[v["grund"]] = gruende.get(v["grund"], 0) + 1
    print("\nHäufigste Ausschlussgründe:")
    for g, n in sorted(gruende.items(), key=lambda x: -x[1])[:12]:
        print(f"  {n:>3}  {g}")


if __name__ == "__main__":
    main()
