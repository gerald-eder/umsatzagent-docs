"""Stufe 2: Gecachte Artikel nach Deutsch übersetzen und als .mdx ausgeben.

Übersetzt nur, was noch nicht übersetzt ist. Das Ergebnis liegt im Cache, ein
zweiter Lauf kostet also nichts. Wer eine Übersetzung neu erzwingen will,
nimmt --force.

    python3 tools/kb/build.py --ordner "Quick Start Guides"
    python3 tools/kb/build.py --limit 5 --trocken
    python3 tools/kb/build.py                       # alles
"""
import argparse, hashlib, json, os, re, sys, time, urllib.parse, urllib.request
import concurrent.futures as cf

sys.path.insert(0, os.path.dirname(__file__))
import config

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, ".kb-cache")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

try:
    from markdownify import markdownify
except ImportError:
    sys.exit("markdownify fehlt:  python3 -m pip install --user markdownify")


# --------------------------------------------------------------------------
# Gemini
# --------------------------------------------------------------------------
def api_key():
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k
    sec = os.path.expanduser("~/.secrets")
    if os.path.exists(sec):
        m = re.search(r'^export GEMINI_API_KEY=["\']?([^"\'\n]+)', open(sec).read(), re.M)
        if m:
            return m.group(1)
    sys.exit("GEMINI_API_KEY nicht gefunden (~/.secrets)")


ANWEISUNG = """Du übersetzt die Hilfe-Artikel einer deutschsprachigen Marketing- und Vertriebssoftware namens UmsatzAgent aus dem Englischen ins Deutsche.

Sprache und Ton:
- Durchgehend "du", nie "Sie".
- Sachlich und knapp. Keine Werbesprache, keine Ausrufezeichen, keine Füllwörter.
- Native deutsche Umlaute: ä ö ü ß. Niemals ae, oe, ue, ss.
- Anleitungen im Imperativ: "Öffne die Einstellungen", nicht "Sie sollten die Einstellungen öffnen".

Struktur — unbedingt einhalten:
- Gib ausschließlich das übersetzte Markdown zurück. Kein Vorwort, keine Erklärung, keine Code-Zäune um das Ganze.
- Übernimm die Struktur exakt: Überschriftenebenen, Listen, Tabellen, Fettungen, Reihenfolge.
- Bilder `![...](...)` bleiben an Ort und Stelle. Die URL änderst du NIE. Alt-Texte übersetzt du.
- Links: die URL bleibt unverändert, nur der sichtbare Text wird übersetzt.
- Code, Platzhalter wie {{contact.name}}, API-Feldnamen und Dateinamen bleiben unverändert.

Produktnamen:
- Das Produkt heißt UmsatzAgent. Meint die Quelle mit "LeadConnector" schlicht die Plattform ("in LeadConnector kannst du…"), schreibe UmsatzAgent.
- ABER: "LeadConnector" bleibt stehen, wo es ein echter Eigenname ist, den der Leser so vorfindet oder eintippen muss — die Mobile App heißt im App Store "Kollab by LeadConnector", und Beschriftungen wie "LC Phone" oder "LC Email" sind Produktnamen. Ersetzt du die, sucht der Leser vergeblich.
- GoHighLevel und HighLevel dürfen nicht vorkommen. Schreibe UmsatzAgent.
- Twilio und Mailgun bleiben stehen. Das sind die tatsächlichen SMS- und E-Mail-Dienste; wer ein Zustellproblem sucht, braucht den Namen.
- Nennt die Quelle einen fremden Support-Kanal (Support-Ticket, Chat, E-Mail-Adresse, Telefonnummer), schreibe stattdessen: "Wende dich an den UmsatzAgent Support."
- Ist ein Satz nur Werbung für einen fremden Marketplace, ein Partnerprogramm oder eine fremde Preisliste, lass ihn weg.

Oberflächenbegriffe — verwende genau diese deutschen Entsprechungen. Sie sind
am Menü der echten App abgelesen; wer davon abweicht, schickt den Leser zu
einem Knopf, den es nicht gibt:
{glossar}

Sonderfälle:
{hinweise}

Übersetze jetzt diesen Artikel. Der Titel steht in der ersten Zeile."""


def uebersetze(titel, markdown, key, modell):
    glossar = "\n".join(f"- {en} → {de}" for en, de in config.GLOSSAR.items())
    hinweise = "\n".join(f"- {h}" for h in config.HINWEISE)
    prompt = ANWEISUNG.format(glossar=glossar, hinweise=hinweise) + f"\n\n# {titel}\n\n{markdown}"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 32768},
    }).encode()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modell}:generateContent?key={key}"
    for versuch in range(4):
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=240))
            cand = d.get("candidates", [{}])[0]
            parts = cand.get("content", {}).get("parts", [])
            txt = "".join(p.get("text", "") for p in parts).strip()
            if txt:
                return txt
            if cand.get("finishReason") in ("SAFETY", "RECITATION"):
                return None
        except Exception:
            time.sleep(3 * (versuch + 1))
    return None


# --------------------------------------------------------------------------
# Aufbereitung
# --------------------------------------------------------------------------
def zu_markdown(html):
    """HTML zu Markdown. Videos überleben als Platzhalter, weil markdownify
    iframes verwirft und die Übersetzung URLs sonst verfremdet."""
    videos = re.findall(r'<iframe[^>]+src="([^"]+)"', html)
    for i, src in enumerate(videos):
        html = re.sub(r"<iframe[^>]+>\s*</iframe>", f"\n\nVIDEOPLATZHALTER{i}\n\n", html, count=1)
    md = markdownify(html, heading_style="ATX", bullets="-", strip=["script", "style"])
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r"[ \t]+\n", "\n", md)
    return md.strip(), videos


def videos_einsetzen(md, videos):
    """Platzhalter durch das Embed ersetzen — und zwar die ganze Zeile.

    Der Platzhalter steht in der Quelle manchmal in einer Überschrift oder
    zwischen Sternchen. Ersetzt man nur ihn, bleibt "## " oder "**" davor
    stehen, und MDX bricht am halb geöffneten JSX-Block ab: die Seite baut
    nicht und liefert live eine 404.
    """
    def embed(src):
        if src.startswith("//"):
            src = "https:" + src
        return (f'<iframe\n  className="w-full aspect-video rounded-xl"\n'
                f'  src="{src}"\n  title="Video"\n  frameborder="0"\n'
                f'  allow="accelerometer; autoplay; clipboard-write; encrypted-media; picture-in-picture"\n'
                f"  allowfullscreen\n></iframe>")

    zeilen = []
    for z in md.split("\n"):
        m = re.search(r"VIDEOPLATZHALTER\s*(\d+)\b", z)
        if not m:
            zeilen.append(z)
            continue
        i = int(m.group(1))
        zeilen.append(embed(videos[i]) if i < len(videos) else "")
    return "\n".join(zeilen)


def marken_ersetzen(text):
    for alt, neu in config.MARKEN:
        text = re.sub(re.escape(alt), neu, text, flags=re.I)
    return text


def restmarken(text):
    """Fremdmarken im sichtbaren Text. URLs bleiben außen vor: Bild-Adressen
    zeigen noch auf die Quelle, werden aber beim Schreiben ersetzt."""
    ohne = re.sub(r"\]\([^)]*\)", "]()", text)          # Link- und Bildziele
    ohne = re.sub(r"https?://\S+", " ", ohne)            # nackte URLs
    low = ohne.lower()
    return sorted({b for b in config.VERBOTEN if b in low})


def bild_holen(url, zielordner):
    endung = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".png"
    if endung not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
        endung = ".png"
    name = hashlib.sha1(url.encode()).hexdigest()[:12] + endung
    pfad = os.path.join(zielordner, name)
    if not os.path.exists(pfad):
        os.makedirs(zielordner, exist_ok=True)
        try:
            req = urllib.request.Request(url, headers=UA)
            data = urllib.request.urlopen(req, timeout=60).read()
            open(pfad, "wb").write(data)
        except Exception:
            return None
    return name


UMLAUT = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"}


def slugify(text, maxlen=70):
    """Dateinamen und Anker bleiben ASCII — so will es die CLAUDE.md-Regel."""
    for a, b in UMLAUT.items():
        text = text.replace(a, b)
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower())
    return text.strip("-")[:maxlen].strip("-")


def aufraeumen(md):
    """Struktur geraderücken, die aus der Quelle schief kommt.

    Die Quelle setzt Überschriften fett und beginnt den Rumpf oft mit H1,
    obwohl der Titel schon im Frontmatter steht. Und das Inhaltsverzeichnis
    zeigt auf die englischen Anker, die es nach der Übersetzung nicht mehr
    gibt — der Linktext trägt aber genau den deutschen Überschriftentext.
    """
    zeilen = []
    for z in md.split("\n"):
        k = re.match(r"^(#{1,6})\s+(.*)$", z)
        if k:
            tiefe, text = k.group(1), k.group(2).strip()
            text = re.sub(r"^\*\*(.*)\*\*$", r"\1", text).strip()
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
            if len(tiefe) == 1:          # H1 gehört dem Frontmatter
                tiefe = "##"
            zeilen.append(f"{tiefe} {text}")
        else:
            zeilen.append(z)
    md = "\n".join(zeilen)

    # Anker aus dem sichtbaren Linktext neu bilden.
    md = re.sub(r"\[([^\]]+)\]\(#[^)]*\)", lambda m: f"[{m.group(1)}](#{slugify(m.group(1), 80)})", md)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


def mdx_sicher(md):
    """Platzhalter vor dem MDX-Parser schützen.

    MDX liest geschweifte Klammern als JavaScript. Ein Platzhalter wie
    {{contact.name}} ist damit ein Syntaxfehler, und die ganze Seite baut
    nicht — sie liefert live eine 404. In Backticks steht er als Code da,
    wird richtig dargestellt und ist obendrein besser lesbar.
    """
    teile = re.split(r"(```.*?```|`[^`\n]*`)", md, flags=re.S)
    for i in range(0, len(teile), 2):          # nur außerhalb von Code
        t = teile[i]
        t = re.sub(r"\{\{([^}\n]{1,120})\}\}", r"`{{\1}}`", t)

        # Spitze Klammern sind in MDX JSX. Der lokale Entwicklungsserver ist
        # da nachsichtig, der Produktions-Build nicht — dort baut die Seite
        # nicht und liefert eine 404.
        t = re.sub(r"<(https?://[^>\s]+)>", r"[\1](\1)", t)      # Markdown-Autolink
        t = re.sub(r"<([^@>\s]+@[^>\s]+)>", r"[\1](mailto:\1)", t)
        t = re.sub(r"<br\s*/?>", "<br/>", t, flags=re.I)          # muss geschlossen sein
        # Alles Übrige — <form>, </body>, <noscript> aus Code-Beispielen ohne
        # Zaun — bleibt als sichtbarer Text stehen statt den Build zu kippen.
        t = re.sub(r"<(?!br/>)(/?[A-Za-z][^>\n]{0,80})>", r"`<\1>`", t)
        # Auffangnetz für alles Übrige — doppelte Klammern, leere Fragmente,
        # ein "<" als Kleiner-als-Zeichen im Fließtext.
        t = re.sub(r"<(?!br/>)", "&lt;", t)
        teile[i] = t
    return "".join(teile)


def frontmatter(titel, beschreibung, quelle):
    def esc(s):
        return s.replace('"', "'").strip()
    return (f'---\ntitle: "{esc(titel)}"\n'
            f'description: "{esc(beschreibung)}"\n'
            f"---\n\n")


def beschreibung_aus(md):
    md = re.sub(r"<iframe.*?</iframe>", " ", md, flags=re.S)
    for zeile in md.split("\n"):
        z = zeile.strip()
        if z and not z.startswith(("#", "!", "|", "-", "*", ">", "<")) and "=" not in z[:30]:
            z = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", z)
            z = re.sub(r"[*_`]", "", z)
            return (z[:155].rsplit(" ", 1)[0] + "…") if len(z) > 158 else z
    return "Anleitung im UmsatzAgent Help Center."


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ordner", help="nur Artikel aus diesem Quell-Ordner")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true", help="Übersetzung erneuern")
    ap.add_argument("--trocken", action="store_true", help="nicht schreiben, nur berichten")
    ap.add_argument("--alles", action="store_true", help="Relevanzauswahl ignorieren")
    ap.add_argument("--modell", default=config.MODELL)
    ap.add_argument("--parallel", type=int, default=4)
    a = ap.parse_args()

    key = api_key()
    struct = json.load(open(os.path.join(CACHE, "struktur.json")))
    os.makedirs(os.path.join(CACHE, "de"), exist_ok=True)

    # Artikel-ID -> Ordnername. Maßgeblich ist die Brotkrume aus zuordnung.py;
    # der Ordner-Crawl kennt nur einen Ausschnitt und wird nur als Notnagel
    # verwendet.
    heimat = {}
    for u, k in struct.items():
        if k["art"] == "ordner":
            for aid in k["artikel"]:
                heimat[aid] = k["name"]
    zpfad = os.path.join(CACHE, "zuordnung.json")
    if os.path.exists(zpfad):
        for aid, v in json.load(open(zpfad)).items():
            heimat[aid] = v["ordner"]
    else:
        print("Hinweis: keine zuordnung.json — erst tools/kb/zuordnung.py laufen lassen,")
        print("         sonst landen hunderte Artikel unter 'Sonstiges'.")

    # Relevanzurteile aus auswahl.py. Fehlen sie, wird alles gebaut.
    apfad = os.path.join(CACHE, "auswahl.json")
    auswahl = json.load(open(apfad)) if os.path.exists(apfad) else {}
    if not auswahl:
        print("Hinweis: keine Auswahl gefunden — es wird alles gebaut.")
        print("         Erst tools/kb/auswahl.py laufen lassen, sonst kommen")
        print("         auch Agentur- und US-Artikel mit.")

    dateien = sorted(os.listdir(os.path.join(CACHE, "articles")))
    posten, verworfen = [], 0
    for f in dateien:
        rec = json.load(open(os.path.join(CACHE, "articles", f)))
        ordner = heimat.get(rec["id"], "Sonstiges")
        if a.ordner and a.ordner.lower() not in ordner.lower():
            continue
        if auswahl and not a.alles:
            urteil = auswahl.get(rec["id"])
            if not urteil or urteil["klasse"] not in config.AUSWAHL_KLASSEN:
                verworfen += 1
                continue
        posten.append((rec, ordner))
    if verworfen:
        print(f"{verworfen} Artikel übersprungen (nicht in {sorted(config.AUSWAHL_KLASSEN)})")
    if a.limit:
        posten = posten[: a.limit]

    print(f"{len(posten)} Artikel zu verarbeiten (Modell {a.modell})")
    if not posten:
        return

    berichte = []

    def eins(paar):
        rec, ordner = paar
        cpfad = os.path.join(CACHE, "de", f'{rec["id"]}.json')
        if os.path.exists(cpfad) and not a.force:
            # Der Ordner wird auch bei Cache-Treffern neu gesetzt: die
            # Zuordnung kann sich seit der Übersetzung verbessert haben,
            # und sie bestimmt, wo die Datei landet.
            return json.load(open(cpfad)) | {"cache": True, "ordner": ordner}

        md, videos = zu_markdown(rec["html"])
        titel_en = rec["titel_en"] or rec["slug"].replace("-", " ").title()

        # Reine Video-Artikel haben keinen übersetzbaren Text. Sie werden
        # angelegt, aber als nachzudrehen markiert: das eingebettete Video
        # zeigt die Fremdmarke, das lässt sich nicht wegübersetzen.
        if videos and len(re.sub(r"VIDEOPLATZHALTER\d+", "", md).split()) < 15:
            nur_titel = uebersetze(titel_en, "(Nur der Titel, kein Rumpf.)", key, a.modell) or titel_en
            nur_titel = marken_ersetzen(nur_titel.lstrip("# ").split("\n")[0].strip())
            erg = {"id": rec["id"], "slug": rec["slug"], "ordner": ordner,
                   "titel": nur_titel, "markdown": md, "videos": videos,
                   "quelle": rec["url"], "rest": [], "nur_video": True, "cache": False}
            json.dump(erg, open(cpfad, "w"), ensure_ascii=False)
            return erg

        de = uebersetze(titel_en, md, key, a.modell)
        if not de:
            return {"id": rec["id"], "fehler": "Übersetzung fehlgeschlagen", "slug": rec["slug"]}

        de = marken_ersetzen(de)
        if de.startswith("#"):
            kopf, _, rest = de.partition("\n")
            titel_de, rumpf = kopf.lstrip("# ").strip(), rest.strip()
        else:
            titel_de, rumpf = marken_ersetzen(titel_en), de
        if not rumpf:
            return {"id": rec["id"], "slug": rec["slug"], "fehler": "leere Übersetzung"}

        erg = {"id": rec["id"], "slug": rec["slug"], "ordner": ordner,
               "titel": titel_de, "markdown": rumpf, "videos": videos,
               "quelle": rec["url"],
               "rest": restmarken(titel_de + "\n" + rumpf), "cache": False}
        json.dump(erg, open(cpfad, "w"), ensure_ascii=False)
        return erg

    with cf.ThreadPoolExecutor(max_workers=a.parallel) as ex:
        for i, erg in enumerate(ex.map(eins, posten), 1):
            berichte.append(erg)
            mark = "cache" if erg.get("cache") else ("FEHLER" if erg.get("fehler") else "neu")
            rest = erg.get("rest") or []
            print(f'  [{i}/{len(posten)}] {mark:>6}  {erg.get("titel", erg.get("slug"))[:64]}'
                  + (f"   ⚠ Fremdmarke: {', '.join(rest)}" if rest else ""))

    gut = [b for b in berichte if not b.get("fehler")]
    mit_rest = [b for b in gut if b.get("rest")]
    nur_video = [b for b in gut if b.get("nur_video")]
    mit_video = [b for b in gut if b.get("videos") and not b.get("nur_video")]
    print(f"\n{len(gut)}/{len(berichte)} übersetzt, {len(mit_rest)} mit Fremdmarken-Rest, "
          f"{len(nur_video)} reine Video-Artikel, {len(mit_video)} mit eingebettetem Video")

    if a.trocken:
        print("Trockenlauf — nichts geschrieben.")
        return

    # --- Ausgabe ----------------------------------------------------------
    # Zielordner leeren. Ändert sich ein Titel, ändert sich der Dateiname —
    # die alte Datei bliebe sonst als Dublette liegen und landete über den
    # Cache sogar wieder in der Navigation.
    npfad = os.path.join(CACHE, "ordnernamen.json")
    ordnernamen = json.load(open(npfad)) if os.path.exists(npfad) else {}

    zielwurzel = os.path.join(ROOT, config.ZIEL)
    if os.path.isdir(zielwurzel) and not a.ordner:
        for wurzel, _, dateien_ in os.walk(zielwurzel):
            for d in dateien_:
                if d.endswith(".mdx"):
                    os.remove(os.path.join(wurzel, d))

    geschrieben = 0
    belegt = {}
    for b in gut:
        # Der Dateiname kommt aus dem deutschen Titel, nicht aus dem Quell-Slug:
        # der trägt die Fremdmarke bis in die URL. Für den Ordner gilt
        # dasselbe — aus "LeadConnector Phone" würde sonst der Pfad
        # /wissen/leadconnector-phone/.
        ordner_de = (ordnernamen.get(b["ordner"])
                     or config.KATEGORIEN.get(b["ordner"])
                     or b["ordner"])
        ordner_slug = slugify(marken_ersetzen(ordner_de), 40)
        art_slug = slugify(b["titel"]) or slugify(b["slug"])
        if belegt.get((ordner_slug, art_slug)):
            art_slug = f'{art_slug}-{b["id"][-4:]}'
        belegt[(ordner_slug, art_slug)] = True

        zielrel = os.path.join(config.ZIEL, ordner_slug, art_slug + ".mdx")
        ziel = os.path.join(ROOT, zielrel)
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        b["pfad"] = zielrel[:-4]  # ohne .mdx, für die Navigation

        md = aufraeumen(b["markdown"])
        if config.BILDER_LOKAL:
            bildordner = os.path.join(ROOT, config.BILDER, b["id"])
            for url in sorted(set(re.findall(r"!\[[^\]]*\]\((https?://[^)\s]+)", md))):
                name = bild_holen(url, bildordner)
                if name:
                    md = md.replace(url, f'/{config.BILDER}/{b["id"]}/{name}')

        md = mdx_sicher(md)
        md = videos_einsetzen(md, b.get("videos") or [])
        text = frontmatter(b["titel"], beschreibung_aus(md), b["quelle"]) + md + "\n"
        open(ziel, "w").write(text)
        geschrieben += 1

        # Pfad zurück in den Cache — die Navigation liest ihn von dort.
        cpfad = os.path.join(CACHE, "de", f'{b["id"]}.json')
        if os.path.exists(cpfad):
            c = json.load(open(cpfad))
            c["pfad"] = b["pfad"]
            c["ordner"] = b["ordner"]
            json.dump(c, open(cpfad, "w"), ensure_ascii=False)

    print(f"{geschrieben} .mdx-Dateien geschrieben nach {config.ZIEL}/")

    # --- Querverweise ------------------------------------------------------
    # Die Artikel verlinken einander über Adressen der Quelle. Die Marken-
    # ersetzung macht daraus Adressen auf unserer Domain, die es dort nicht
    # gibt. Aus der Artikelnummer in der Adresse lässt sich aber ableiten,
    # wohin der Verweis bei uns gehört.
    pfad_von_id = {b["id"]: b["pfad"] for b in gut if b.get("pfad")}
    quelle_muster = re.compile(
        r"\((?:https?://)?(?:support|help|app)?\.?umsatzagent\.com/[^)\s]*?/articles/(\d+)[^)\s]*\)")

    intern = tot = 0

    def ersetze(m):
        nonlocal intern
        ziel = pfad_von_id.get(m.group(1))
        if ziel:
            intern += 1
            return f"(/{ziel})"
        return m.group(0)

    for b in gut:
        if not b.get("pfad"):
            continue
        p = os.path.join(ROOT, b["pfad"] + ".mdx")
        text = open(p).read()
        neu = quelle_muster.sub(ersetze, text)
        # Was übrig bleibt, zeigt auf einen nicht übernommenen Artikel. Der
        # Link käme im Nichts an, also bleibt nur der Text stehen.
        neu, n = re.subn(
            r"\[([^\]]+)\]\((?:https?://)?(?:support|help|app)?\.?umsatzagent\.com/[^)\s]*?/articles/\d+[^)\s]*\)",
            r"\1", neu)
        tot += n
        if neu != text:
            open(p, "w").write(neu)

    if intern or tot:
        print(f"Querverweise: {intern} auf interne Seiten umgebogen, "
              f"{tot} ins Leere zeigende entschärft")

    bericht = os.path.join(CACHE, "nacharbeit.json")
    json.dump({"fremdmarke": [{"slug": b["slug"], "begriffe": b["rest"]} for b in mit_rest],
               "nur_video": [{"slug": b["slug"], "videos": b.get("videos")} for b in nur_video],
               "mit_video": [{"slug": b["slug"], "videos": b.get("videos")} for b in mit_video]},
              open(bericht, "w"), ensure_ascii=False, indent=1)

    if mit_rest:
        print("\nNacharbeit — diese Artikel nennen noch eine Fremdmarke:")
        for b in mit_rest:
            print(f'  {b["slug"]}: {", ".join(b["rest"])}')
    if nur_video or mit_video:
        print(f"\nNacharbeit — {len(nur_video) + len(mit_video)} Artikel binden fremde Videos ein.")
        print("  Die zeigen die Quellmarke im Bild; das lässt sich nicht übersetzen.")
        print(f"  Liste: {bericht}")


if __name__ == "__main__":
    main()
