#!/usr/bin/env python3
"""Package an approved reel for hand-posting: output/<id>/ + a TextEdit note.

    python pack.py 07-cheers

Local only — output/ is gitignored on purpose. The note carries the caption to
paste, the comment to post AND PIN BY HAND (the API cannot pin), the licence
obligations split into required vs courtesy, and the script's `avoid` field.
"""
import json, re, shutil, sys
import publish
from pipeline import config as C


def pack(sid):
    spec = json.loads((C.SCRIPTS / f"{sid}.json").read_text())
    led  = json.loads(C.LEDGER.read_text()) if C.LEDGER.exists() else {}
    mine = {f: v for f, v in led.get("credits", {}).items() if f.startswith(sid + "-")}
    must = [v for v in mine.values() if "cc by" in v.lower()]
    courtesy = [v for v in mine.values() if v not in must]

    d = C.OUTPUT / sid; d.mkdir(exist_ok=True)
    for name in (f"{sid}.mp4", f"{sid}.raw.mp4"):   # finished reel + its untouched render
        loose = C.OUTPUT / name
        if loose.exists():
            shutil.move(str(loose), str(d / name))

    caption = publish.caption_with_credits(sid, spec)   # same function the API post uses

    L = [f"{spec['title_hi']}  ({spec['title_en']})",
         f"{sid}   ·   {spec['theme']}   ·   hook: {spec['hook_archetype']}", "",
         "="*60, "CAPTION  —  paste this into Instagram", "="*60, caption, "",
         "="*60, "COVER", "="*60,
         ("The opening text is burned into the video from the very first frame:\n  "
          + "  /  ".join(spec["hook_text"])
          + "\nIn the Instagram cover picker, choose the FIRST frame."
          if spec.get("hook_text") else "No opening text on this reel."), "",
         "="*60, "PINNED COMMENT  —  post as a comment, then PIN it",
         "(the API cannot pin; this has to be done by hand)", "="*60,
         publish.source_comment(sid, spec), "",
         "="*60, "LICENCE OBLIGATIONS", "="*60]
    if must:
        L += ["REQUIRED — these CC licences oblige you to name creator + licence.",
              "Keep BOTH the caption line and the pinned comment: the caption is",
              "permanent, a comment can be deleted or un-pinned.", ""]
        L += [f"  * {v}" for v in sorted(must)]
    else:
        L.append("NONE. No CC BY / CC BY-SA material — add nothing to the caption.")
    if courtesy:
        L += ["", "Public domain / CC0 (courtesy, not obligation):"]
        L += [f"  - {v}" for v in sorted(courtesy)]
    L += ["", "Stock b-roll: Pexels (no attribution required).", "",
          "="*60, "BEFORE YOU POST", "="*60, spec.get("avoid", "(none)")]
    (d / f"{sid}-notes.txt").write_text("\n".join(L), encoding="utf-8")
    print(f"  {sid}/  mp4 + notes   ({len(must)} required credit(s))")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    for s in sys.argv[1:]:
        pack(s)
