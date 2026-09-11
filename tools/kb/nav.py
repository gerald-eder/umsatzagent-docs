"""Stufe 3: Navigation in docs.json aus den gebauten Artikeln erzeugen.

Die handgeschriebenen Seiten (Start, Anna, Konto) bleiben unangetastet — sie
stehen in BESTAND und werden vorangestellt. Alles darunter kommt aus der
Wissensdatenbank und wird bei jedem Lauf neu erzeugt.

    python3 tools/kb/nav.py
    python3 tools/kb/nav.py --trocken
"""
import argparse, html, json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
import config

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, ".kb-cache")

# Vorangestellte Gruppen. Aktuell nur die Startseite.
#
# Bis 09.09.2026 standen hier dreizehn weitere Seiten über Onboarding, Anna,
# Plattform und Abrechnung. Sie waren maschinell geschrieben und von niemandem
# gegengelesen; die Abrechnungsseite nannte Monatspreis, sechs Add-On-Preise
# und Verbrauchstarife auf zwei Nachkommastellen. Die Zahlen stimmten zwar mit
# PRODUCT/ANNA/knowledgebase-2026-08.md überein, aber ungeprüfte Preiszusagen
# gehören nicht ins Help Center, und Preise bekommen ohnehin eine eigene Seite.
#
# Die Dateien liegen weiter im Repo und in der Historie. Wer sie
# zurückholen will, trägt sie hier wieder ein — nach dem Gegenlesen.
BESTAND = [
    {"group": "Start", "pages": ["index"]},
]

# Dauerhafte Links in der Seitenleiste, auf JEDER Seite sichtbar.
#
# Der Grund für Anchors statt einer reinen Linkliste auf der Startseite: Wer in
# einem Artikel feststeckt, kommt von dort direkt zum Call oder in die Community,
# ohne den Weg zurück zur Startseite zu suchen. Was hinter diesen Links liegt —
# Kurse, Community, Rechnungen — wohnt im GoHighLevel-Portal und braucht Login;
# es lässt sich hier nicht nachbauen und soll es auch nicht.
GLOBAL_ANCHORS = [
    {"anchor": "Kurse", "icon": "graduation-cap",
     "href": "https://portal.umsatzagent.com"},
    {"anchor": "Community", "icon": "comments",
     "href": "https://portal.umsatzagent.com/communities/groups/umsatzai-community/home"},
    {"anchor": "Weekly Q&A-Call", "icon": "calendar-days",
     "href": "https://click.umsatzagent.com/widget/bookings/weekly-q-a-call"},
    {"anchor": "Support-Call", "icon": "headset",
     "href": "https://click.umsatzagent.com/widget/bookings/umsatzagent-support"},
    {"anchor": "App öffnen", "icon": "arrow-up-right-from-square",
     "href": "https://app.umsatzagent.com"},
]

# Die Leiste oben rechts. Sie trägt bewusst nur zwei Ziele.
#
# Anchors allein reichen nicht: Sie stehen oben in der Seitenleiste, und die
# springt zum aktuellen Artikel. Auf einer tief einsortierten Seite liegen sie
# dadurch rund 1600 Pixel über dem Bildrand — gemessen, nicht geschätzt. Wer
# über Google in einem Artikel landet, sieht sie nie. Die Navbar scrollt nicht
# weg und ist damit der einzige Weg, der auch dort noch funktioniert.
NAVBAR = {
    "links": [
        {"label": "Kurse", "href": "https://portal.umsatzagent.com"},
    ],
    "primary": {
        "type": "button",
        "label": "Support-Call",
        "href": "https://click.umsatzagent.com/widget/bookings/umsatzagent-support",
    },
}

# Aus der Navigation genommen, bis jemand sie gegengelesen hat.
UNGEPRUEFT = [
    "fuer-inhaber", "fuer-team",
    "erste-schritte/ueberblick", "erste-schritte/onboarding",
    "erste-schritte/was-du-beitraegst",
    "anna/ueberblick", "anna/im-chat", "anna/am-telefon",
    "plattform/ueberblick", "plattform/integrationen",
    "konto/abrechnung", "konto/vertrag", "konto/datenschutz",
]


def ordner_deutsch(namen):
    """Ordnernamen einmalig übersetzen und im Cache festhalten.

    Was in config.KATEGORIEN steht, gewinnt — das ist die von Hand gesetzte
    Wahrheit. Der Rest geht einmal durch das Modell.
    """
    pfad = os.path.join(CACHE, "ordnernamen.json")
    karte = json.load(open(pfad)) if os.path.exists(pfad) else {}
    offen = [n for n in namen if n and n not in karte and n not in config.KATEGORIEN]

    if offen:
        sys.path.insert(0, os.path.dirname(__file__))
        import build
        liste = "\n".join(f"{i+1}. {n}" for i, n in enumerate(offen))
        frage = ("Übersetze diese Rubriken einer deutschsprachigen Marketing-Software "
                 "ins Deutsche. Knapp, wie eine Menü-Beschriftung, ohne Artikel. "
                 "Etablierte englische Fachbegriffe (Workflow, Funnel, Pipeline, Opportunity, "
                 "Snapshot, Dashboard) bleiben stehen. Fremdmarken wie LeadConnector oder "
                 "HighLevel ersetzt du durch UmsatzAgent.\n"
                 "Antworte als nummerierte Liste, gleiche Reihenfolge, nur die Übersetzungen.\n\n"
                 + liste)
        antwort = build.uebersetze("Rubriken", frage, build.api_key(), config.MODELL) or ""
        for zeile in antwort.split("\n"):
            m = re.match(r"\s*(\d+)[.)]\s*(.+)", zeile)
            if m:
                i = int(m.group(1)) - 1
                if 0 <= i < len(offen):
                    karte[offen[i]] = build.marken_ersetzen(m.group(2).strip())
        json.dump(karte, open(pfad, "w"), ensure_ascii=False, indent=1)
        print(f"{len([n for n in offen if n in karte])}/{len(offen)} Ordnernamen übersetzt")

    return lambda n: config.KATEGORIEN.get(n) or karte.get(n) or n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trocken", action="store_true")
    a = ap.parse_args()

    struct = json.load(open(os.path.join(CACHE, "struktur.json")))

    # Ordner -> Kategorie, und Ordner-ID -> Name
    ordner_name, kat_von_ordner = {}, {}
    for u, k in struct.items():
        if k["art"] == "ordner":
            m = re.search(r"folders/(\d+)", u)
            if m:
                ordner_name[m.group(1)] = html.unescape(k["name"] or "")
    for u, k in struct.items():
        if k["art"] == "kategorie":
            for fid in k["ordner"]:
                kat_von_ordner[ordner_name.get(fid, "")] = html.unescape(k["name"] or "")

    # Die Brotkrume kennt die Zuordnung vollständig, der Ordner-Crawl nicht.
    zpfad = os.path.join(CACHE, "zuordnung.json")
    if os.path.exists(zpfad):
        for v in json.load(open(zpfad)).values():
            kat_von_ordner[v["ordner"]] = v["kategorie"]

    # Gebaute Artikel einsammeln: Ordnername -> [(titel, pfad)]
    nach_ordner = {}
    for f in sorted(os.listdir(os.path.join(CACHE, "de"))):
        b = json.load(open(os.path.join(CACHE, "de", f)))
        if b.get("fehler") or not b.get("pfad"):
            continue
        if not os.path.exists(os.path.join(ROOT, b["pfad"] + ".mdx")):
            continue
        nach_ordner.setdefault(html.unescape(b["ordner"]), []).append((b["titel"], b["pfad"]))

    if not nach_ordner:
        sys.exit("Keine gebauten Artikel gefunden — erst tools/kb/build.py laufen lassen.")

    # Ordner den Themen zuordnen
    thema_von_kat = {}
    for thema, kats in config.THEMEN:
        for k in kats:
            thema_von_kat[k] = thema

    eindeutschen = ordner_deutsch(sorted(nach_ordner))

    gruppen, ohne_thema = {}, []
    for ordner, artikel in nach_ordner.items():
        kat = kat_von_ordner.get(ordner, "")
        if kat in config.AUSGESCHLOSSEN:
            continue
        thema = thema_von_kat.get(kat)
        if not thema:
            ohne_thema.append((ordner, kat))
            thema = "Weitere Themen"
        gruppen.setdefault(thema, {}).setdefault(eindeutschen(ordner), []).extend(artikel)

    # In Mintlify-Navigation gießen
    reihenfolge = [t for t, _ in config.THEMEN] + ["Weitere Themen"]
    wissen = []
    for thema in reihenfolge:
        if thema not in gruppen:
            continue
        unter = []
        for ordner, artikel in sorted(gruppen[thema].items()):
            seiten = [p for _, p in sorted(artikel)]
            # Ein Ordner mit einem einzigen Artikel braucht keine eigene Ebene.
            if len(seiten) == 1:
                unter.append(seiten[0])
            else:
                unter.append({"group": ordner, "pages": seiten})
        wissen.append({"group": thema, "pages": unter})

    anzahl = sum(len(a) for g in gruppen.values() for a in g.values())
    print(f"{anzahl} Artikel in {len(wissen)} Themen")
    for g in wissen:
        n = sum(len(p["pages"]) if isinstance(p, dict) else 1 for p in g["pages"])
        print(f'  {n:>4}  {g["group"]}')
    if ohne_thema:
        print("\nOhne Themen-Zuordnung (landen unter 'Weitere Themen'):")
        for o, k in sorted(set(ohne_thema)):
            print(f"  Ordner {o!r} aus Kategorie {k!r}")

    if a.trocken:
        print("\nTrockenlauf — docs.json unverändert.")
        return

    # Zwei Tabs statt einer langen Leiste: Der Hub beantwortet "wohin?", die
    # Anleitungen beantworten "wie?". In einer gemeinsamen Liste standen beide
    # untereinander und sahen gleich wichtig aus.
    p = os.path.join(ROOT, "docs.json")
    d = json.load(open(p))
    d["navigation"] = {
        "global": {"anchors": GLOBAL_ANCHORS},
        "tabs": [
            {"tab": "Start", "icon": "house", "pages": ["index"]},
            # Der Symptom-Einstieg steht vor den Funktionsgruppen: Wer ein
            # Problem hat, weiß selten, in welchem Bauteil es steckt.
            {"tab": "Anleitungen", "icon": "book-open",
             "groups": ([{"group": "Hilfe bei Problemen",
                          "pages": ["wissen/etwas-funktioniert-nicht"]}]
                        if os.path.exists(os.path.join(ROOT, "wissen",
                                                       "etwas-funktioniert-nicht.mdx"))
                        else []) + wissen},
        ],
    }
    d["navbar"] = NAVBAR
    json.dump(d, open(p, "w"), ensure_ascii=False, indent=2)
    open(p, "a").write("\n")
    print(f"\ndocs.json aktualisiert — 2 Tabs, {len(GLOBAL_ANCHORS)} Anchors, Navbar")


if __name__ == "__main__":
    main()
