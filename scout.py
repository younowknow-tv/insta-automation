#!/usr/bin/env python3
"""Sourceability scout — is a subject filmable, BEFORE we script it?

    python scout.py "Gyan Chaupar" "samosa" "Bakhshali manuscript"

Month one kept discovering mid-render that the imagery did not exist: three
samosa clips on all of Pexels, "smallpox eradication India" returning a camel,
moksha patam returning nothing at all. Each of those cost a full render to find.
Counts alone lie — a query always returns *something* — so this prints the top
titles too, because the title is what reveals a near-miss.
"""
import re, sys
from pipeline import fetch


def _key(term):
    """The word a result must actually contain to be about this subject."""
    words = [w for w in re.findall(r"[A-Za-z]{4,}", term)]
    return max(words, key=len).lower() if words else term.lower()


def scout(term):
    key   = _key(term)
    vid   = fetch.candidates(term, want=6)
    photo = fetch._pexels_photos(term, set(), None, want=6)
    comm  = fetch._commons(term, set(), None, want=6)

    def rel(hits):
        return [h for h in hits if key in h["title"].lower()]

    rv, rp, rc = rel(vid), rel(photo), rel(comm)
    # counts are meaningless here — these APIs always return SOMETHING. What
    # matters is how many results actually name the subject.
    if len(rc) >= 2:                    verdict = "STRONG   archival names it"
    elif len(rv) >= 2:                  verdict = "OK       stock video names it"
    elif rv or rp or rc:                verdict = "THIN     few real matches"
    else:                               verdict = "NONE     nothing names it"

    print(f"\n{'='*70}\n{term}    (key word: '{key}')\n  -> {verdict}\n{'='*70}")
    for label, hits, rl in (("commons", comm, rc), ("video", vid, rv), ("photo", photo, rp)):
        print(f"  {label:<8} {len(rl)} of {len(hits)} actually name '{key}'")
        for h in rl[:3]:
            t = h["title"].replace("https www pexels com video ", "")[:54]
            print(f"           {h.get('size','?'):>11}  {t}")
        if not rl and hits:
            print(f"           (all near-misses, e.g. {hits[0]['title'][:44]})")
    return verdict

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    rows = [(t, scout(t)) for t in sys.argv[1:]]
    print(f"\n{'='*68}\nSUMMARY\n{'='*68}")
    for t, v in rows:
        print(f"  {v.split()[0]:<8} {t}")
