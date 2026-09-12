"""B-roll fetch with a used-asset ledger, so no shot repeats within a month.

Two lessons from the first render, both of which put the wrong food on screen:

  * `orientation=portrait` silently discards the best footage. The renderer
    crops to fill, so a 4K landscape clip is fine — and on narrow subjects it is
    often the ONLY real match. Rank portrait first, never exclude landscape.
  * Neither API understands a long descriptive query; both keyword-match and
    Pixabay ORs the terms, so "samosa indian food" returns ocean waves. A beat
    can therefore name a `must` keyword that has to appear in the result's own
    title, which is the only relevance signal these APIs expose.
"""
import json, re, requests
from . import config as C

STOP = {"a", "an", "the", "of", "in", "on", "with", "and", "close", "up", "shot",
        "shallow", "depth", "field", "single", "scene", "view"}


def _ledger():
    return json.loads(C.LEDGER.read_text()) if C.LEDGER.exists() else {"used": []}


def _remember(uid, dest):
    # Also map file -> uid, so the publisher can credit the providers a given
    # video actually pulled from rather than crediting both every time.
    l = _ledger()
    l["used"].append(uid)
    l.setdefault("assets", {})[dest.name] = uid
    C.LEDGER.write_text(json.dumps(l, indent=1))


def _slug(v):
    """Pexels puts the human title in the URL; it is the only description we get."""
    return re.sub(r"[^a-z0-9]+", " ", (v.get("url") or "").lower())


def _score(v, query, must):
    """Higher is better. -1 means reject."""
    slug = _slug(v)
    if must and must.lower() not in slug:
        return -1
    words = {w for w in re.findall(r"[a-z]+", query.lower()) if w not in STOP}
    hits = sum(1 for w in words if w in slug)
    h, w = v.get("height", 0), v.get("width", 0)
    portrait = 2 if h > w else 0            # prefer, do not require
    return hits * 10 + portrait + min(h, 2160) / 10000


def _pexels(q, used, must=None, want=1):
    if not C.PEXELS_KEY:
        return []
    r = requests.get("https://api.pexels.com/videos/search",
                     headers={"Authorization": C.PEXELS_KEY},
                     params={"query": q, "per_page": 30}, timeout=30)
    if r.status_code != 200:
        return []
    out = []
    for v in r.json().get("videos", []):
        uid = f"pexels:{v['id']}"
        if uid in used:
            continue
        s = _score(v, q, must)
        if s < 0:
            continue
        files = [f for f in v["video_files"] if f.get("height", 0) >= 1080]
        if not files:
            continue
        # Take the LARGEST sensible rendition, not the smallest: a landscape clip
        # gets upscaled and heavily cropped to fill 9:16, so spare pixels are the
        # difference between a sharp frame and a soft one. Cap at 4K.
        best = sorted(files, key=lambda f: -min(f["height"], 2160))[0]
        out.append({"uid": uid, "url": best["link"], "score": s,
                    "title": _slug(v).strip(), "page": v.get("url", ""),
                    "size": f"{v['width']}x{v['height']}"})
    return sorted(out, key=lambda c: -c["score"])[:want]


def _pixabay(q, used, must=None, want=1):
    """Pixabay ORs its terms, so without a `must` it happily returns nonsense."""
    if not C.PIXABAY_KEY:
        return []
    r = requests.get("https://pixabay.com/api/videos/",
                     params={"key": C.PIXABAY_KEY, "q": q, "per_page": 30}, timeout=30)
    if r.status_code != 200:
        return []
    out = []
    for v in r.json().get("hits", []):
        uid = f"pixabay:{v['id']}"
        if uid in used:
            continue
        tags = (v.get("tags") or "").lower()
        if must and must.lower() not in tags:
            continue
        vids = v.get("videos", {})
        link = (vids.get("large") or vids.get("medium") or {}).get("url")
        if link:
            out.append({"uid": uid, "url": link, "score": 0, "title": tags,
                        "page": v.get("pageURL", ""), "size": "?"})
    return out[:want]


def _pexels_photos(q, used, must=None, want=1):
    """Stills. Far deeper catalogue than video for specific dishes, and `alt`
    gives a real caption to match against instead of a URL slug."""
    if not C.PEXELS_KEY:
        return []
    r = requests.get("https://api.pexels.com/v1/search",
                     headers={"Authorization": C.PEXELS_KEY},
                     params={"query": q, "per_page": 40}, timeout=30)
    if r.status_code != 200:
        return []
    out = []
    for p in r.json().get("photos", []):
        uid = f"pexelsphoto:{p['id']}"
        if uid in used:
            continue
        desc = f"{p.get('alt','')} {p.get('url','')}".lower()
        if must and must.lower() not in desc:
            continue
        words = {w for w in re.findall(r"[a-z]+", q.lower()) if w not in STOP}
        hits = sum(1 for w in words if w in desc)
        src = p.get("src", {})
        link = src.get("original") or src.get("large2x")
        if link:
            out.append({"uid": uid, "url": link, "score": hits * 10,
                        "title": (p.get("alt") or "")[:70], "page": p.get("url", ""),
                        "size": f"{p.get('width')}x{p.get('height')}", "photo": True})
    return sorted(out, key=lambda c: -c["score"])[:want]


def candidates(query, must=None, want=6):
    """Ranked options for a query, for human review before anything downloads."""
    used = set(_ledger()["used"])
    return _pexels(query, used, must, want) + _pixabay(query, used, must, want)


def clip(query: str, dest, must=None, kind="video"):
    """Download the best unused asset for `query`. Returns path or None.

    kind="photo" pulls a still instead; the renderer gives it the same slow push
    as footage, which is what makes a stills sequence read as deliberate.
    """
    if dest.exists():
        return dest
    for cand in (dest.parent.glob(dest.stem + ".*")):
        if cand.exists():
            return cand
    used = set(_ledger()["used"])
    if kind == "photo":
        hits = _pexels_photos(query, used, must, want=1)
    elif kind == "auto":
        # motion first — a stills sequence reads as a slideshow next to footage
        hits = candidates(query, must, want=1) or _pexels_photos(query, used, must, want=1)
    else:
        hits = candidates(query, must, want=1)
    if not hits:
        print(f"  !! no clip for: {query}" + (f"  (must contain '{must}')" if must else ""))
        return None
    c = hits[0]
    if c.get("photo"):
        dest = dest.with_suffix(".jpg")
    dest.write_bytes(requests.get(c["url"], timeout=180).content)
    _remember(c["uid"], dest)
    print(f"  b-roll {c['uid']:<20} {c['title'][:48]}")
    return dest
