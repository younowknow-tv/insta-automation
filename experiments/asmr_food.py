#!/usr/bin/env python3
"""One-off: a silent ASMR kadhi-chawal reel, cut from four phone clips.

    python experiments/asmr_food.py

Not part of the daily pipeline. No voice, no captions, no music — the track
goes on in the Instagram app, so the MP4 ships with a silent stereo stream
(a video-only file gives the app nothing to lay music against). Unbranded:
this is for a new channel, not now_you_know.tv.

THE FOUR SOURCES
----------------
Three serving clips shot in 4K, handheld, well lit (the pot with its chilli
tadka, the ladle, the thecha, the finished plate), and then twelve minutes of
eating, shot in 1080 from one fixed overhead angle on a wooden table.

They are different films. The serving clips have real coverage and good colour
and need almost nothing. The eating clip has one angle, flat indoor light and
no cutaways, and everything below is the answer to that.

1. No coverage. Every "shot" from the eating clip is a crop of the same frame.
   Pushing in to different parts of the plate at different zooms is the only
   thing that makes a cut read as a cut rather than as a jump.

2. The table is dull and it is 40% of the frame. Rather than matte the plate
   (a hand crosses the rim constantly, and a cutout would slice the wrist), the
   background is replaced by compositing through a feathered ellipse:
   - CUTOUT   — only where no hand is in frame. The plate is masked at its rim,
     shrunk, given a soft drop shadow and set on defocused fog, so it floats.
     Used twice: entering the meal, and the clean plate at the end.
   - VIGNETTE — wherever a hand appears. A frame-sized ellipse with a wide
     feather, so the table dissolves into fog towards the corners and a wrist
     entering frame fades into it instead of being cut in half.
   One mask generator, two sets of numbers.

   The vignette earns its keep twice over now: the kitchen counter and the
   dining table are two different rooms, and dissolving both into the same fog
   is what makes them read as one film.

3. Nothing happens for minutes at a time. The edit keeps only the moments that
   are events — tadka stirred in, kadhi poured, bite lifted — and runs the
   eating between them at 5-30x. Roughly 70% of the runtime is 1x or slower.

Three things earlier passes got wrong, all worth not repeating:

  * blend=screen was run in YUV. Screen pushes values up, and on the U and V
    planes that means both chroma channels at once — which is magenta. Any
    blend that is not a per-plane-safe mode has to be done in RGB.
  * Mist was screen-blended over the WHOLE frame, which lifts the blacks until
    the food goes milky and a white plate clips to pink. Mist now goes into the
    background before the food is composited over it.
  * The eating clip was graded warm globally, which took the rice and the hand
    with it. selectivecolor does it properly: see GRADE_WARM.

NOT USED: the last ten seconds of IMG_7806 are a child eating, including their
face. Left out deliberately — the channel rule is no faces, and a child is not
ours to publish. Everything before 0:13 of that clip is plate footage and is in.
"""
import subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C

W, H, FPS = C.W, C.H, C.FPS
OUT = C.OUTPUT / "experiments"
GROUND = C.ASSETS / "asmr-mist.mp4"         # fog over a dark valley: warm food needs a cool ground
MIST = C.ASSETS / "asmr-steam.mp4"

# This is for a NEW channel, not now_you_know.tv, so it ships unbranded: no
# logo watermark and no NYK endcard. Set BRAND to a PNG path to put a mark back.
BRAND = None

# The dish name over the clean plate at the end. CHANNEL is empty until the new
# channel is named; set it and it prints under the dish, smaller.
TITLE = ("KADHI", "CHAWAL")
CHANNEL = ""

DL = Path.home() / "Downloads"
POT = DL / "IMG_7804.MOV"       # 4K: the pot, the tadka, the ladle, plating
THECHA = DL / "IMG_7805.MOV"    # 4K: the thecha going on
PLATED = DL / "IMG_7806.MOV"    # 4K: the finished plate (first 13s only)
EATING = DL / "IMG_8003.MOV"    # 1080, 12 min, one fixed overhead angle

# Plate geometry for the EATING clip, measured off frames at 0:02 and 6:56 and
# nudged a few px inside the rim. That camera never moves, so these are
# constants — no tracking. (The 4K clips are handheld and never masked.)
PLATE1 = (529, 697, 500, 554)      # cx, cy, semi-axis x, semi-axis y
PLATE2 = (532, 997, 508, 566)
PLATE3 = (517, 905, 503, 598)      # same plate at the end, nudged by the eating

# Roughly 70% of the runtime is at 1x or slower. The fast passes are there to
# skip the parts where nothing happens, not to set the tempo — an ASMR cut that
# is fast all the way through has nothing to be slow against.
#
# The 4K clips run at zoom 1.0: they were framed by hand for a phone screen and
# are already tight, so cropping them only risks clipping the action. Zoom is a
# repair for the eating clip, which was not framed for anything.
SHOTS = [
    # --- served ----------------------------------------------------------
    dict(name="01-tadka",   src="POT",    ss=0.6,   dur=3.0, speed=1.0,
         zoom=1.0, c=(540, 960), grade="light", push=(1.00, 1.06)),
    dict(name="02-ladle",   src="POT",    ss=9.8,   dur=2.6, speed=0.8,
         zoom=1.0, c=(540, 960), grade="light"),
    dict(name="03-pour",    src="POT",    ss=13.4,  dur=2.2, speed=1.0,
         zoom=1.0, c=(540, 960), grade="light"),
    dict(name="04-pakora",  src="POT",    ss=27.0,  dur=2.0, speed=0.85,
         zoom=1.0, c=(540, 960), grade="light"),
    dict(name="05-thecha",  src="THECHA", ss=1.6,   dur=2.8, speed=1.0,
         zoom=1.0, c=(540, 960), grade="light"),
    dict(name="06-plated",  src="PLATED", ss=0.6,   dur=2.4, speed=1.0,
         zoom=1.0, c=(540, 960), grade="light", push=(1.00, 1.05)),
    # --- eaten -----------------------------------------------------------
    dict(name="07-hero",    ss=1.2,   dur=2.6,  speed=0.75, style="cutout",
         plate=PLATE1, push=(1.00, 1.09)),
    dict(name="08-bite-a",  ss=45.2,  dur=3.6,  speed=1.0,  zoom=1.45, c=(529, 697)),
    dict(name="09-mix-a",   ss=62.0,  dur=20.0, speed=5.0,  zoom=1.30, c=(529, 690)),
    dict(name="10-bite-b",  ss=122.4, dur=3.6,  speed=1.0,  zoom=1.42, c=(520, 690)),
    dict(name="11-mix-b",   ss=436.0, dur=16.0, speed=5.0,  zoom=1.32, c=(531, 990)),
    dict(name="12-lapse",   ss=490.0, dur=110.0, speed=30.0, zoom=1.18, c=(520, 930)),
    # --- finished --------------------------------------------------------
    # The clean plate floats like the full one did, and the dish name lands on
    # it. exp pulls the white plate back from clipping under the warm grade.
    dict(name="13-clean",   ss=727.0, dur=4.3,  speed=0.8,  style="cutout",
         plate=PLATE3, push=(1.00, 1.05), exp=-0.045, title=True),
]

SOURCES = {"POT": POT, "THECHA": THECHA, "PLATED": PLATED}

# The phone shot this under cool indoor light, so the kadhi came out a pale
# greenish yellow. selectivecolor is doing the work a global warm-up cannot:
# it pulls cyan out of the YELLOWS and REDS and adds magenta, which turns the
# kadhi gold and brings the tadka specks forward, while leaving WHITES alone so
# the rice stays rice. The curves pair finishes the white balance; the highlight
# points keep the plate from clipping, and a stronger push than this (tested)
# turns both the kadhi orange and the hand with it.
GRADE_WARM = ("selectivecolor="
              "yellows=-0.17 0.11 0.21 0.02:"
              "reds=-0.19 0.13 0.21 -0.02:"
              "neutrals=-0.03 0.015 0.035 0,"
              "curves=r='0/0 0.4/0.44 0.85/0.89 1/1':b='0/0 0.4/0.355 0.85/0.88 1/1',"
              "eq=contrast=1.12:saturation=1.20,"
              "unsharp=5:5:0.5:5:5:0.0")

# The 4K clips were shot in good warm light and the kadhi in them is already
# gold with a real chilli tadka on it. Running GRADE_WARM over them would cook
# them orange, so they get a fraction of the same move and nothing else.
#
# The two grades have to MEET, which is why GRADE_WARM is milder than it was
# when the eating clip stood alone. Graded to look its best by itself, it cut
# to the 4K footage with visibly pinker rice and a pinker hand. Continuity
# across a cut beats either shot winning on its own.
GRADE_LIGHT = ("selectivecolor=yellows=-0.08 0.05 0.11 0:reds=-0.08 0.05 0.09 0,"
               "eq=contrast=1.09:saturation=1.15,"
               "unsharp=5:5:0.40:5:5:0.0")

GRADES = {"warm": GRADE_WARM, "light": GRADE_LIGHT}


def _dur(p):
    return float(subprocess.run([C.FFPROBE, "-v", "quiet", "-show_entries",
                                 "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout.strip())


def _mask(path, cx, cy, ax, ay, feather):
    """A white feathered ellipse on black, used as an alpha channel.

    `feather` is in normalised ellipse units: 0.03 is a hard cut at the plate
    rim, 0.32 is the dissolve that lets a wrist fade into the background.
    """
    expr = f"255*clip((1-hypot((X-{cx})/{ax}\\,(Y-{cy})/{ay}))/{feather}\\,0\\,1)"
    subprocess.run([C.FFMPEG, "-y", "-loglevel", "error",
                    "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}",
                    "-vf", f"format=gray,geq=lum='{expr}'",
                    "-frames:v", "1", str(path)], check=True)


def _background(seed):
    """Fog over a dark valley, with wisps drifting through it.

    The mist is crushed with a curve first so only the bright wisps survive —
    screen-blending the raw smoke clip just raises the black level everywhere.
    """
    return [
        # cover 1440x2160 first, so there is room to drift inside the 1080x1920 crop
        f"[1:v]scale=1440:2160:force_original_aspect_ratio=increase,crop=1440:2160,"
        f"crop={W}:{H}:x='180+150*sin(t*0.25+{seed})':y='90+80*cos(t*0.19+{seed})',"
        f"gblur=sigma=24,eq=brightness=-0.03:saturation=0.95,vignette=PI/3.5,"
        f"fps={FPS},format=gbrp[bgraw]",
        f"[2:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"setpts=PTS*2.0,fps={FPS},curves=all='0/0 0.35/0 0.7/0.5 1/1',"
        f"format=gbrp[mist]",
        # blend in RGB, NOT yuv: screen-mode on the U and V planes pushes both
        # chroma channels up at once, which is how the first pass turned the
        # whole background magenta.
        "[bgraw][mist]blend=all_mode=screen:all_opacity=0.50:shortest=1,"
        "format=yuv420p[bg]",
    ]


def _title_ass(path, out_dur):
    """The dish name, set on the clean plate.

    Dark on the plate rather than white over it: the plate is the brightest
    thing in frame, so white would need an outline and an outline would make it
    a caption. Two lines because twelve letters at this size do not fit on one,
    and the point of the note was that it should be big.
    """
    hold = max(0.6, out_dur - 0.05)
    lines = [(1.10, 772, TITLE[0]), (1.28, 962, TITLE[1])]
    if CHANNEL:
        lines.append((1.70, 1180, CHANNEL))
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n"
            "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
            "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,"
            "BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
            # warm charcoal (&H00BBGGRR), no outline, a soft shadow for lift
            "Style: Dish,Avenir Next,170,&H0020242A,&H0020242A,&H00FFFFFF,&H70FFFFFF,"
            "1,0,0,0,100,100,14,0,1,0,3,5,0,0,0,1\n"
            "Style: Chan,Avenir Next,54,&H0040444A,&H0040444A,&H00FFFFFF,&H70FFFFFF,"
            "0,0,0,0,100,100,10,0,1,0,2,5,0,0,0,1\n\n[Events]\n"
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    body = "".join(
        f"Dialogue: 0,{_ts(t)},{_ts(hold)},{'Chan' if txt == CHANNEL else 'Dish'},"
        f",0,0,0,,{{\\fad(520,0)\\pos({W // 2},{y})}}{txt}\n"
        for t, y, txt in lines)
    Path(path).write_text(head + body, encoding="utf-8")


def _ts(t):
    h, rem = divmod(max(0.0, t), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def shot(src, s, tmp, i):
    out = tmp / f"{s['name']}.mp4"
    out_dur = s["dur"] / s["speed"]
    style = s.get("style", "vignette")

    cmd = [C.FFMPEG, "-y", "-loglevel", "error",
           "-ss", f"{s['ss']}", "-t", f"{s['dur']}", "-i", str(src),
           "-stream_loop", "-1", "-i", str(GROUND),
           "-stream_loop", "-1", "-i", str(MIST)]
    fc = _background(i * 1.7)

    if style == "cutout":
        cx, cy, ax, ay = s["plate"]
        m = tmp / f"mask-{s['name']}.png"
        _mask(m, cx, cy, ax, ay, 0.03)
        cmd += ["-loop", "1", "-i", str(m)]
        sw, sh = int(W * 0.86) // 2 * 2, int(H * 0.86) // 2 * 2
        # Shrinking the whole frame keeps the plate wherever it sat in it —
        # which for plate one is 36% down, leaving a third of the reel empty.
        # Nudge the layer so the plate itself lands at 44% height, not the frame —
        # high enough to clear the caption and buttons Instagram draws at the foot.
        sc = sh / H
        dx = int(round(W * 0.50 - ((W - sw) / 2 + cx * sc)))
        dy = int(round(H * 0.44 - ((H - sh) / 2 + cy * sc)))
        fc += [
            f"[0:v]fps={FPS},scale={W}:{H},setsar=1,"
            f"setpts=(PTS-STARTPTS)/{s['speed']},format=yuv420p[f]",
            f"[3:v]scale={W}:{H},format=gray,split=2[m1][m2]",
            f"[f][m1]alphamerge,scale={sw}:{sh}[plate]",
            # a soft drop shadow, so the plate sits in the fog
            # instead of looking pasted on top of it
            f"[m2]scale={sw}:{sh},gblur=sigma=30[shm]",
            f"color=c=black:s={sw}x{sh}:r={FPS}[shc]",
            "[shc][shm]alphamerge[shadow]",
            f"[bg][shadow]overlay=(W-w)/2+{dx}:(H-h)/2+{dy + 26}:shortest=1[bgs]",
            f"[bgs][plate]overlay=(W-w)/2+{dx}:(H-h)/2+{dy}:shortest=1[comp]",
        ]
    else:
        z = s["zoom"]
        cw, ch = int(W / z) // 2 * 2, int(H / z) // 2 * 2
        cx, cy = s["c"]
        x = max(0, min(W - cw, cx - cw // 2))
        y = max(0, min(H - ch, cy - ch // 2))
        m = tmp / "mask-vignette.png"
        if not m.exists():
            _mask(m, W // 2, H // 2, 700, 1210, 0.32)
        cmd += ["-loop", "1", "-i", str(m)]
        fc += [
            # scale to 1080x1920 BEFORE the crop, so one set of crop numbers
            # works for the 1080 eating clip and the 4K serving clips alike
            f"[0:v]fps={FPS},scale={W}:{H},crop={cw}:{ch}:{x}:{y},scale={W}:{H},"
            f"setsar=1,setpts=(PTS-STARTPTS)/{s['speed']},format=yuv420p[f]",
            f"[3:v]scale={W}:{H},format=gray[m]",
            "[f][m]alphamerge[fa]",
            "[bg][fa]overlay=0:0:shortest=1[comp]",
        ]

    grade = GRADES[s.get("grade", "warm")]
    tail = f"[comp]" + (f"eq=brightness={s['exp']}," if s.get("exp") else "") + grade
    if s.get("push"):
        z0, z1 = s["push"]
        n = max(2, int(round(out_dur * FPS)))
        tail += (f",zoompan=z='{z0}+({z1 - z0})*on/{n}':d=1:"
                 f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}")
    if s.get("title"):
        # after the zoompan, so the type stays rock steady while the shot moves
        a = tmp / "title.ass"
        _title_ass(a, out_dur)
        tail += f",ass={a}"

    if BRAND:
        cmd += ["-loop", "1", "-i", str(BRAND)]
        fc += [tail + "[gr]",
               "[4:v]scale=150:-1,colorkey=0x000000:0.32:0.05,format=rgba,"
               "colorchannelmixer=aa=0.40[lg]",
               "[gr][lg]overlay=(W-w)/2:86:shortest=1[v]"]
    else:
        fc += [tail + "[v]"]

    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]",
            "-t", f"{out_dur:.3f}", "-an",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)]
    subprocess.run(cmd, check=True)
    print(f"  {s['name']:<10} {s['dur']:>6.1f}s src @{s['speed']:>5}x -> {_dur(out):4.1f}s")
    return out


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    missing = [p for p in (POT, THECHA, PLATED, EATING) if not p.exists()]
    if missing:
        raise SystemExit("missing source clip(s):\n  " +
                         "\n  ".join(str(p) for p in missing))
    parts = [shot(SOURCES.get(s.get("src"), EATING), s, tmp, i)
             for i, s in enumerate(SHOTS)]

    # No endcard. The NYK card belongs to the other channel, and ending on the
    # empty floating plate loops straight back into the full one.

    out = OUT / "asmr-kadhi.mp4"
    cmd = [C.FFMPEG, "-y", "-loglevel", "error"]
    for p in parts:
        cmd += ["-i", str(p)]
    cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
    chain = "".join(f"[{i}:v]" for i in range(len(parts)))
    cmd += ["-filter_complex", f"{chain}concat=n={len(parts)}:v=1:a=0[v]",
            "-map", "[v]", "-map", f"{len(parts)}:a", "-shortest",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    print(f"\n  -> {out}  {_dur(out):.1f}s  {out.stat().st_size / 1e6:.1f}MB")
    return out


if __name__ == "__main__":
    build()
