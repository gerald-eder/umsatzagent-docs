"""Stufe 1: Artikel und Struktur von der Quelle holen und im Cache ablegen.

Holt nur, was noch fehlt. Ein zweiter Lauf ist billig und ergänzt Neues.

    python3 tools/kb/pull.py            # alles
    python3 tools/kb/pull.py --limit 10 # Probelauf
"""
import argparse, json, os, re, sys, time
import urllib.request, urllib.error
import concurrent.futures as cf

sys.path.insert(0, os.path.dirname(__file__))
import config

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, ".kb-cache")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(1.5 * (i + 1))
        except Exception:
            time.sleep(1.5 * (i + 1))
    return None


def clean_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    if not m:
        return None
    t = re.sub(r"\s+", " ", m.group(1)).strip()
    t = re.sub(r"\s*[|:]\s*(Support\s*)?:?\s*LeadConnector\s*$", "", t)
    return t.strip(" |:")


def article_body(html):
    m = re.search(r'<article[^>]*class="[^"]*article-body[^"]*"[^>]*>(.*?)</article>', html, re.S)
    return m.group(1).strip() if m else ""


def slug_of(url):
    tail = url.rstrip("/").split("/")[-1]
    m = re.match(r"(\d+)-(.*)", tail)
    return (m.group(1), m.group(2)) if m else (tail, tail)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    os.makedirs(os.path.join(CACHE, "articles"), exist_ok=True)

    sm = get(config.SITEMAP)
    if not sm:
        sys.exit("Sitemap nicht erreichbar")
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    arts = [u for u in locs if "/solutions/articles/" in u]
    cats = [u for u in locs if re.search(r"/solutions/\d+", u)]
    folds = [u for u in locs if "/solutions/folders/" in u]
    print(f"Sitemap: {len(arts)} Artikel, {len(folds)} Ordner, {len(cats)} Kategorien")

    # --- Struktur ---------------------------------------------------------
    struct_path = os.path.join(CACHE, "struktur.json")
    if a.force or not os.path.exists(struct_path):
        struct = {}
        with cf.ThreadPoolExecutor(max_workers=10) as ex:
            for kind, urls in (("kategorie", cats), ("ordner", folds)):
                for u, html in zip(urls, ex.map(get, urls)):
                    if not html:
                        continue
                    struct[u] = {
                        "art": kind,
                        "name": clean_title(html),
                        "artikel": sorted(set(re.findall(r"/solutions/articles/(\d+)", html))),
                        "ordner": sorted(set(re.findall(r"/solutions/folders/(\d+)", html))),
                    }
        json.dump(struct, open(struct_path, "w"), ensure_ascii=False, indent=1)
        print(f"Struktur gespeichert: {len(struct)} Knoten")
    else:
        struct = json.load(open(struct_path))
        print(f"Struktur aus Cache: {len(struct)} Knoten")

    # --- Artikel ----------------------------------------------------------
    if a.limit:
        arts = arts[: a.limit]

    todo = []
    for u in arts:
        aid, slug = slug_of(u)
        p = os.path.join(CACHE, "articles", f"{aid}.json")
        if a.force or not os.path.exists(p):
            todo.append((u, aid, slug, p))

    print(f"Zu holen: {len(todo)} von {len(arts)}")
    ok = fail = 0

    def work(item):
        u, aid, slug, p = item
        html = get(u)
        if not html:
            return ("404", u)
        body = article_body(html)
        if not body:
            return ("leer", u)
        rec = {
            "id": aid, "slug": slug, "url": u,
            "titel_en": clean_title(html),
            "html": body,
            "bilder": re.findall(r'<img[^>]+src="([^"]+)"', body),
        }
        json.dump(rec, open(p, "w"), ensure_ascii=False)
        return ("ok", u)

    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for i, (status, u) in enumerate(ex.map(work, todo), 1):
            if status == "ok":
                ok += 1
            else:
                fail += 1
                print(f"  {status}: {u}")
            if i % 50 == 0:
                print(f"  … {i}/{len(todo)}")

    print(f"\nFertig: {ok} geholt, {fail} fehlgeschlagen")
    print(f"Cache: {CACHE}")


if __name__ == "__main__":
    main()
