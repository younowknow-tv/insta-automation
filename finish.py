#!/usr/bin/env python3
"""Finishing pass: opening text + flicker into the tagline, on a rendered reel.

    python finish.py 05-shunya 07-cheers        # finish banked reels in output/<id>/
    python finish.py --fit 05-shunya 11-terahvin  # print fitted text sizes, no encode

Replaces the hand-edit Gaurav was doing in the Instagram app before posting:
  * a two-line hook on the opening frames, big enough to read on a phone, and
    visible from frame 0 so any cover picker gets the text (a fade-in would make
    frame 0 blank)
  * a flicker over the last half-second of narration, cutting clean to the
    tagline card — "cut + transition", placed before the tagline

It works on a finished MP4 instead of inside render.py, so it can be applied to
approved reels WITHOUT re-rendering them: their approved voice and visuals stay
byte-identical underneath. The untouched render is kept as <id>.raw.mp4 and the
pass always runs from it, so running twice never stacks two layers.
"""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path
from pipeline import config as C

MAX_PX, READABLE_PX = 170, 120      # font size cap, and the floor below which we flag
SAFE_W = 1080 - 2 * 80              # brand/style.md: 80px left/right safe margins
ACCENT = "&H0000D7FF&"              # gold, BGR order — ASS colours are &HBBGGRR


def _dur(p):
    return float(subprocess.run([C.FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], capture_output=True, text=True,
                                check=True).stdout.strip())


def _ass(lines, size, playx=1080, playy=1920, x=540, y=640, end="0:00:03.20"):
    body = "\\N".join(lines[:1] + [f"{{\\c{ACCENT}}}{l}" for l in lines[1:]])
    # Spacing MUST stay 0: any letter-spacing breaks Devanagari shaping into dotted circles
    return (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {playx}\nPlayResY: {playy}\n"
            f"WrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
            "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
            "Alignment,MarginL,MarginR,MarginV,Encoding\n"
            f"Style: Hook,{C.CAPTION_FONT},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,"
            f"1,0,0,0,100,100,0,0,1,{max(6, size // 16)},3,5,0,0,0,1\n\n[Events]\n"
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
            f"Dialogue: 0,0:00:00.00,{end},Hook,,0,0,0,,{{\\pos({x},{y})\\fad(0,250)}}{body}\n")


def _width(line, size):
    """True rendered width of one line, measured with libass + HarfBuzz shaping."""
    with tempfile.TemporaryDirectory() as t:
        a = Path(t) / "m.ass"
        a.write_text(_ass([line], size, playx=3200, playy=600, x=1600, y=300, end="0:00:01.00"),
                     encoding="utf-8")
        err = subprocess.run([C.FFMPEG, "-hide_banner", "-f", "lavfi", "-i",
                              "color=black:s=3200x600:d=0.2", "-vf",
                              f"ass={a},cropdetect=limit=24:round=2:reset=0", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
    m = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", err)
    return int(m[-1][0]) if m else 0


def fit(lines):
    """One size for both lines: the largest that keeps the WIDER line inside the safe width."""
    widest = max(_width(l, MAX_PX) for l in lines)
    size = MAX_PX if widest <= SAFE_W else int(MAX_PX * SAFE_W / widest)
    return size, widest


def finish(sid, src, dst):
    spec = json.loads((C.SCRIPTS / f"{sid}.json").read_text())
    assert spec["beats"][-1]["mode"] == "FIXED", f"{sid}: last beat is not the fixed tagline"
    total, tagline = _dur(src), _dur(C.TAGLINE)
    tag = round(total - tagline, 3)           # tag is always last and voiced by brand/tagline.wav
    assert 20 < tag < total, f"{sid}: implausible tagline start {tag}"

    vf, note = [], ""
    if spec.get("hook_text"):
        size, _ = fit(spec["hook_text"])
        hook = C.ASSETS / f"{sid}.hook.ass"
        hook.write_text(_ass(spec["hook_text"], size), encoding="utf-8")
        vf.append(f"ass={hook}")
        note = f"hook {size}px" + ("  !! BELOW READABLE — shorten the line" if size < READABLE_PX else "")
    fs = round(tag - 0.5, 3)
    vf.append(f"eq=brightness='if(between(t,{fs},{tag}),if(lt(mod(t*16,2),1),0.55,-0.45),0)':eval=frame")

    tmp = Path(dst).with_suffix(".finishing.mp4")
    subprocess.run([C.FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
                    "-vf", ",".join(vf), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(tmp)],
                   check=True)
    os.replace(tmp, dst)
    print(f"  finished {Path(dst).name}  flicker {fs:.2f}-{tag:.2f}s  {note}")
    return dst


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(1)
    if args[0] == "--fit":
        for sid in args[1:]:
            lines = json.loads((C.SCRIPTS / f"{sid}.json").read_text()).get("hook_text")
            if not lines:
                print(f"  {sid:<16} no hook_text"); continue
            size, widest = fit(lines)
            flag = "  !! below readable" if size < READABLE_PX else ""
            print(f"  {sid:<16} {size:>3}px  (widest line {widest}px at {MAX_PX}px){flag}")
        sys.exit(0)
    for sid in args:
        d = C.OUTPUT / sid
        final, raw = d / f"{sid}.mp4", d / f"{sid}.raw.mp4"
        if not raw.exists():
            final.rename(raw)                 # keep the approved, unfinished render
        finish(sid, raw, final)
