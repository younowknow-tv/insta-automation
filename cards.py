#!/usr/bin/env python3
"""Static feed cards — 1080x1350 PNGs built from a JSON spec.

    python cards.py shabd-shampoo billi-record         # -> output/static/<id>[-N].png
    python cards.py --all

Reels reach people; cards are what they save. Same discipline as the reels:
every card carries its source line in the image, and Wikimedia credits are
collected automatically (the ledger keys off the "<id>-" filename prefix, so
`publish.commons_credits(<id>)` works for cards exactly as it does for reels).

Built on ffmpeg + libass rather than PIL because Devanagari conjuncts (क्ष, त्र,
ज्ञ) need HarfBuzz shaping — the same reason render.py burns captions this way.

4:5 is deliberate: it takes the most vertical space Instagram allows in feed.
"""
import json, os, subprocess, sys, tempfile
from pathlib import Path
from pipeline import config as C
from pipeline import fetch

W, H = 1080, 1350
OUT = C.OUTPUT / "static"
SPECS = C.ROOT / "content" / "cards"
LOGO = C.ROOT / "brand" / "profile" / "pfp-nyk.png"
ACCENT = "&H0000D7FF&"          # gold, BGR — same accent as the reel hook text
MUTED = "&H00A8A8A8&"


def _ass(slide):
    """One card's text. Styles mirror brand/style.md: 80px side margins, Spacing 0
    (any letter-spacing breaks Devanagari shaping into dotted circles)."""
    def esc(s):
        return s.replace("{", "(").replace("}", ")").replace("\n", " ")

    title = slide["title"]
    head = "\\N".join([esc(title[0])] + [f"{{\\c{ACCENT}}}{esc(l)}" for l in title[1:]])
    style = ("Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
             "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
             "Alignment,MarginL,MarginR,MarginV,Encoding\n")
    for name, size, colour, outline in (("Series", 44, ACCENT, 3), ("Title", 104, "&H00FFFFFF", 5),
                                        ("Body", 58, "&H00FFFFFF", 4), ("Source", 32, MUTED, 3)):
        style += (f"Style: {name},{C.CAPTION_FONT},{size},{colour},{colour},&H00000000,&H64000000,"
                  f"1,0,0,0,100,100,0,0,1,{outline},2,5,90,90,0,1\n")

    ev = []
    if slide.get("series"):
        ev.append(f"{{\\pos({W//2},250)}}{esc(slide['series'])}|Series")
    ev.append(f"{{\\pos({W//2},{slide.get('title_y', 560)})}}{head}|Title")
    if slide.get("body"):
        ev.append(f"{{\\pos({W//2},{slide.get('body_y', 900)})}}{esc(slide['body'])}|Body")
    if slide.get("source"):
        ev.append(f"{{\\pos({W//2},1270)}}{esc(slide['source'])}|Source")

    lines = "\n".join(f"Dialogue: 0,0:00:00.00,0:00:10.00,{t.split('|')[-1]},,0,0,0,,{t.rsplit('|', 1)[0]}"
                      for t in ev)
    return (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n"
            f"WrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n{style}\n[Events]\n"
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n" + lines + "\n")


def _background(slide, cid, n):
    """Archival image where the card has one, flat ink where it does not."""
    # ffmpeg's color filter wants 0xRRGGBB; a leading # silently yields black
    ink = slide.get("bg", "#0d0d10").replace("#", "0x")
    img = slide.get("image")
    if not img:
        return f"color=c={ink}:s={W}x{H}", []
    dest = C.ASSETS / f"{cid}-{n}.jpg"
    got = fetch.clip(img["q"], dest, must=img.get("must"), kind=img.get("kind", "commons"))
    if not got:
        return f"color=c={slide.get('bg', '#0d0d10')}:s={W}x{H}", []
    return None, [str(got)]


def build(cid):
    spec = json.loads((SPECS / f"{cid}.json").read_text())
    slides = spec.get("slides") or [spec]
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for n, slide in enumerate(slides):
        slide.setdefault("series", spec.get("series"))
        src, inputs = _background(slide, cid, n)
        with tempfile.TemporaryDirectory() as t:
            a = Path(t) / "card.ass"
            a.write_text(_ass(slide), encoding="utf-8")
            cmd = [C.FFMPEG, "-y", "-hide_banner", "-loglevel", "error"]
            if src:
                cmd += ["-f", "lavfi", "-i", src]
            else:
                cmd += ["-i", inputs[0]]
            cmd += ["-i", str(LOGO)]
            # fill 4:5, dim so white text holds, then text, then logo
            fc = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"eq=brightness=-0.16:saturation=0.90,"
                  f"drawbox=x=0:y=0:w={W}:h={H}:color=black@{slide.get('dim', 0.42)}:t=fill,"
                  f"ass={a}[t];[1:v]scale=132:-1[logo];[t][logo]overlay=(W-w)/2:70")
            dst = OUT / (f"{cid}.png" if len(slides) == 1 else f"{cid}-{n + 1}.png")
            cmd += ["-filter_complex", fc, "-frames:v", "1", str(dst)]
            subprocess.run(cmd, check=True)
        made.append(dst)
        print(f"  card {dst.name}")
    return made


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(1)
    ids = sorted(p.stem for p in SPECS.glob("*.json")) if args[0] == "--all" else args
    for cid in ids:
        build(cid)
