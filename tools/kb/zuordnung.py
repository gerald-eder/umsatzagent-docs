"""Stufe 1b: Kategorie und Ordner je Artikel aus der Brotkrume holen.

Die Ordnerseiten der Quelle listen nur einen Ausschnitt ihrer Artikel — ein
Ordner mit 69 Artikeln zeigt fünf davon und einen "View all"-Link, und
`?page=2` wird ignoriert. Wer die Zuordnung allein daraus baut, verliert
hunderte Artikel ins Nichts.

Die Artikelseite selbst weiß es besser: ihre Brotkrume nennt Kategorie und
Ordner. Diese Stufe holt genau das, und nur für Artikel, deren Zuordnung noch
fehlt.

    python3 tools/kb/zuordnung.py
"""
import argparse, html, json, os, re, sys, time
import urllib.request, urllib.error
import concurrent.futures as cf

sys.path.insert(0, os.path.dirname(__file__))
import config

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, ".kb-cache")
ZIEL = os.path.join(CACHE, "zuordnung.json")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def get(url, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def brotkrume(html_text):
    m = re.search(r'<div class="breadcrumb">(.*?)</div>', html_text, re.S)
    if not m:
        return None, None
    glieder = re.findall(r'<a href="(/support/solutions[^"]*)"[^>]*>(.*?)</a>', m.group(1), re.S)
    kategorie = ordner = None
    for href, name in glieder:
        name = html.unescape(re.sub(r"\s+", " ", name)).strip()
        if re.search(r"/solutions/folders/\d+", href):
            ordner = name
        elif re.search(r"/solutions/\d+", href):
            kategorie = name
    return kategorie, ordner


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--parallel", type=int, default=6)
    a = ap.parse_args()

    karte = {} if a.force else (json.load(open(ZIEL)) if os.path.exists(ZIEL) else {})

    arts = []
    for f in sorted(os.listdir(os.path.join(CACHE, "articles"))):
        r = json.load(open(os.path.join(CACHE, "articles", f)))
        if r["id"] not in karte:
            arts.append((r["id"], r["url"]))

    print(f"{len(arts)} Artikel ohne Zuordnung")
    if not arts:
        print("Nichts zu tun.")
        return

    def hol(paar):
        aid, url = paar
        h = get(url)
        if not h:
            return aid, None, None
        return (aid,) + brotkrume(h)

    ok = 0
    with cf.ThreadPoolExecutor(max_workers=a.parallel) as ex:
        for i, (aid, kat, ordner) in enumerate(ex.map(hol, arts), 1):
            if kat or ordner:
                karte[aid] = {"kategorie": kat or "Sonstiges", "ordner": ordner or "Sonstiges"}
                ok += 1
            if i % 50 == 0:
                print(f"  … {i}/{len(arts)}  ({ok} zugeordnet)")
                json.dump(karte, open(ZIEL, "w"), ensure_ascii=False, indent=1)

    json.dump(karte, open(ZIEL, "w"), ensure_ascii=False, indent=1)
    print(f"\n{ok} neu zugeordnet, {len(karte)} insgesamt")

    kats = {}
    for v in karte.values():
        kats[v["kategorie"]] = kats.get(v["kategorie"], 0) + 1
    print(f"\n{len(kats)} Kategorien:")
    for k, n in sorted(kats.items(), key=lambda x: -x[1])[:15]:
        print(f"  {n:>4}  {k}")


if __name__ == "__main__":
    main()
