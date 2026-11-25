#!/usr/bin/env python3
"""One-off: turn a long locked-off eating video into a silent ASMR food reel.

    python experiments/asmr_food.py ~/Downloads/IMG_8003.MOV

Not part of the daily pipeline. No voice, no captions, no music — Gaurav adds
the track in the Instagram app, so the MP4 ships with a silent stereo stream
(a video-only file gives the app nothing to lay music against).

WHY IT LOOKS THE WAY IT DOES
----------------------------
The source is twelve minutes of one fixed top-down shot: a plate of kadhi-pakora
and rice on a wooden table, eaten by hand. One camera, one angle, no cutaways.
Three problems follow from that, and this script is the answer to them.

1. No coverage. Every "shot" is a crop of the same frame. Pushing in to
   different parts of the plate at different zooms is the only thing that makes
   a cut read as a cut rather than as a jump.

2. The table is dull and it is 40% of the frame. Rather than matte the plate
   (a hand crosses the rim constantly, and a cutout would slice the wrist), the
   background is replaced by compositing through a feathered ellipse:
   - CUTOUT   — only where no hand is in frame. The plate is masked at its rim,
     shrunk, given a soft drop shadow and set on defocused fog. The
     plate genuinely floats. Used twice: the opening, and the second helping.
   - VIGNETTE — wherever a hand appears. A frame-sized ellipse with a wide
     feather, so the table dissolves into fog towards the corners and a
     wrist entering frame fades into it instead of being cut in half.
   One mask generator, two sets of numbers.

3. Nothing happens for minutes at a time. The edit keeps only the moments that
   are events — plate lands, rice added, chutney spooned on, bite lifted — and
   runs the eating between them at 6-40x.

Two things the first pass got wrong, both fixed here and worth not repeating:

  * Mist was screen-blended over the WHOLE frame. Screen lifts blacks, so the
    food went milky and the white plate blew out to pink. Mist is now blended
    into the background only, before the food is composited over it — so it
    drifts behind the plate and never touches it.
  * The background was warm autumn bokeh, which merged with warm food into
    orange soup. It is now fog over a dark valley: the plate is the only warm thing
    in frame, which is what makes it read as food.

The plate changes partway through (there is a second helping at 6:51 in the
source). That is kept, not hidden — its arrival is the midpoint beat.
"""
import subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C

W, H, FPS = C.W, C.H, C.FPS
OUT = C.OUTPUT / "experiments"
GROUND = C.ASSETS / "asmr-mist.mp4"         # fog over a dark valley: warm food needs a cool ground
MIST = C.ASSETS / "asmr-steam.mp4"
LOGO = C.ROOT / "brand" / "profile" / "pfp-nyk.png"

# Plate geometry, measured off frames at 0:02 and 6:56 and nudged a few px
# inside the rim. The camera never moves, so these are constants — no tracking.
PLATE1 = (529, 697, 500, 554)      # cx, cy, semi-axis x, semi-axis y
PLATE2 = (532, 997, 508, 566)
PLATE3 = (517, 905, 503, 598)      # same plate at the end, nudged by the eating

SHOTS = [
    # --- plate one -------------------------------------------------------
    dict(name="01-hero",    ss=1.2,   dur=1.9,  speed=0.75, style="cutout",
         plate=PLATE1, push=(1.00, 1.08)),
    dict(name="02-bite-a",  ss=45.9,  dur=2.5,  speed=1.0,  zoom=1.45, c=(529, 697)),
    dict(name="03-mix-a",   ss=60.0,  dur=24.0, speed=8.0,  zoom=1.30, c=(529, 690)),
    dict(name="04-bite-b",  ss=123.0, dur=2.2,  speed=1.0,  zoom=1.42, c=(520, 690)),
    # --- plate two: the second helping -----------------------------------
    dict(name="05-lands",   ss=411.55, dur=1.35, speed=1.0,  zoom=1.10, c=(531, 980)),
    dict(name="06-float",   ss=415.2, dur=1.6,  speed=0.8,  style="cutout",
         plate=PLATE2, push=(1.07, 1.00)),
    dict(name="07-rice",    ss=420.4, dur=2.4,  speed=1.0,  zoom=1.25, c=(531, 980)),
    dict(name="08-chutney", ss=427.0, dur=1.3,  speed=0.5,  zoom=1.22, c=(531, 950)),
    dict(name="09-mix-b",   ss=434.0, dur=18.0, speed=6.0,  zoom=1.32, c=(531, 990)),
    # --- the plate goes clean --------------------------------------------
    dict(name="10-lapse",   ss=480.0, dur=120.0, speed=40.0, zoom=1.18, c=(520, 930)),
    # bookend: the reel opens on a full plate floating in fog and closes on
    # the same plate wiped clean. exp pulls the white plate back from clipping.
    dict(name="11-clean",   ss=727.6, dur=2.6,  speed=0.8,  style="cutout",
         plate=PLATE3, push=(1.00, 1.06), exp=-0.045),
]

# Deeper shadows and a touch more colour, but no red push: the first pass used
# colorbalance to "warm" the image and turned the white plate pink.
GRADE = ("eq=contrast=1.10:saturation=1.22:brightness=0.005,"
         "curves=all='0/0 0.28/0.24 0.72/0.76 1/1',"
         "colorbalance=rs=0.015:bs=-0.022:rm=0.01:bm=-0.015,"
         "unsharp=5:5:0.45:5:5:0.0")


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
            f"[0:v]fps={FPS},crop={cw}:{ch}:{x}:{y},scale={W}:{H},setsar=1,"
            f"setpts=(PTS-STARTPTS)/{s['speed']},format=yuv420p[f]",
            f"[3:v]scale={W}:{H},format=gray[m]",
            "[f][m]alphamerge[fa]",
            "[bg][fa]overlay=0:0:shortest=1[comp]",
        ]

    tail = f"[comp]" + (f"eq=brightness={s['exp']}," if s.get("exp") else "") + GRADE
    if s.get("push"):
        z0, z1 = s["push"]
        n = max(2, int(round(out_dur * FPS)))
        tail += (f",zoompan=z='{z0}+({z1 - z0})*on/{n}':d=1:"
                 f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}")

    cmd += ["-loop", "1", "-i", str(LOGO)]
    fc += [tail + "[gr]",
           "[4:v]scale=150:-1,colorkey=0x000000:0.32:0.05,format=rgba,"
           "colorchannelmixer=aa=0.40[lg]",
           "[gr][lg]overlay=(W-w)/2:86:shortest=1[v]"]

    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]",
            "-t", f"{out_dur:.3f}", "-an",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)]
    subprocess.run(cmd, check=True)
    print(f"  {s['name']:<10} {s['dur']:>6.1f}s src @{s['speed']:>5}x -> {_dur(out):4.1f}s")
    return out


def build(src):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    parts = [shot(src, s, tmp, i) for i, s in enumerate(SHOTS)]

    # endcard trimmed to 2s: four seconds of brand card at the end of a 30s
    # ASMR loop is dead air, and these reels live on the rewatch.
    end = tmp / "end.mp4"
    subprocess.run([C.FFMPEG, "-y", "-loglevel", "error", "-i", str(C.ENDCARD),
                    "-t", "2.0", "-vf", f"scale={W}:{H},fps={FPS},setsar=1",
                    "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", str(end)], check=True)
    parts.append(end)

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
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    build(Path(sys.argv[1]).expanduser())
