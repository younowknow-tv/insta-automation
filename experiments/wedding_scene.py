#!/usr/bin/env python3
"""One-off: put the two people from IMG_8076 at an Indian wedding instead of a cafe.

    python experiments/wedding_scene.py

Keeps the subjects — both people, the table, the food, every gesture — and
replaces the room behind them.

HOW THE MATTE IS MADE
---------------------
Apple's Vision framework (`PersonMask.swift`, compiled on first run) produces a
person matte per frame. It runs locally, needs no model download, and is
trained for exactly this: people. 297 frames take about 40 seconds.

A person matte alone is not enough, because the subjects are EATING: the table
and the plates are part of the subject and Vision does not mark them. Cut on
the person matte alone and two people float in mid-air with their hands over
nothing.

The fix relies on the camera being locked — checked by differencing the first
and last frame, where the whole table region comes back flat. So the keep-mask
is the union of:

  * the per-frame person matte, and
  * a static half-plane below the table's far edge: y = 795 + 0.12x, feathered
    over 28px, measured off a gridded frame.

Everything below that line is kept as shot. That is deliberate and it is the
honest limit of this approach: the chairs are below the line. Replace them and
the woman is sitting on thin air. So the venue can only ever appear in the band
above the table — and in this framing the subjects fill about 85% of the frame,
so that band is thin.

WHICH IS WHY THE BACKDROP IS A FLOWER WALL
------------------------------------------
Tried first, and rejected by eye: a wedding hall interior, a decorated stage,
a banquet room. Blurred down to a thin band behind two heads, all three read as
"a warm blurry room" and nothing more. Hanging marigold garlands read as an
Indian wedding even as a sliver in the corner of frame, because the colour and
the vertical strands are the signal. Blur stays low (sigma 4) for the same
reason: blur it to sigma 8 and the cue is gone.

Two things that make a composite stop looking pasted, both cheap:

  * LIGHT WRAP. A band just inside the subject edge, lit with the colour of the
    background behind it. Built by subtracting a blurred copy of the alpha from
    the alpha itself, which leaves exactly that inner band, then screening the
    blurred background through it.
  * One grade over the whole composite at the end, so subject and backdrop sit
    in the same light rather than being two correctly-exposed strangers.

NOTE ON THE PEOPLE: this is Gaurav's own footage of identifiable adults. Their
faces are in frame throughout, which is his call to make, not a default.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C

HERE = Path(__file__).resolve().parent
W, H, FPS = C.W, C.H, C.FPS
OUT = C.OUTPUT / "experiments"
SRC = Path.home() / "Downloads" / "IMG_8076.MOV"

BACKDROP = C.ASSETS / "wed-garland.mp4"   # hanging marigold garlands
BACKDROP_AT = 3.0                         # the one frame of it we hang behind them
BOKEH = C.ASSETS / "wed-bokeh.mp4"        # golden bokeh on black, for the lights

MASK_W, MASK_H = 720, 1280   # Vision's matte is coarse; full res buys nothing
BLUR = 4                     # low on purpose: see the docstring
TABLE_LINE = (795, 0.12, 28)  # intercept, slope, feather — y = 795 + 0.12x


def _dur(p):
    return float(subprocess.run([C.FFPROBE, "-v", "quiet", "-show_entries",
                                 "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout.strip())


def _personmask_bin(tmp):
    """Compile the Vision matte tool once, into the temp dir."""
    exe = tmp / "personmask"
    src = HERE / "PersonMask.swift"
    subprocess.run(["swiftc", "-O", str(src), "-o", str(exe)], check=True)
    return exe


def _mattes(tmp):
    frames, masks = tmp / "fr", tmp / "mk"
    frames.mkdir(); masks.mkdir()
    subprocess.run([C.FFMPEG, "-y", "-loglevel", "error", "-i", str(SRC),
                    "-vf", f"fps={FPS},scale={MASK_W}:{MASK_H}",
                    str(frames / "%04d.png")], check=True)
    n = len(list(frames.glob("*.png")))
    print(f"  {n} frames -> Vision person matte")
    subprocess.run([str(_personmask_bin(tmp)), str(frames), str(masks)], check=True)
    return masks


def _table_mask(path):
    """White below the table's far edge, black above, feathered across it."""
    b, m, f = TABLE_LINE
    expr = f"255*clip((Y-({b}+{m}*X))/{f}\\,0\\,1)"
    subprocess.run([C.FFMPEG, "-y", "-loglevel", "error",
                    "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}",
                    "-vf", f"format=gray,geq=lum='{expr}'",
                    "-frames:v", "1", str(path)], check=True)


def build():
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}")
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    try:
        masks = _mattes(tmp)
        below = tmp / "below.png"
        _table_mask(below)

        wall = tmp / "wall.png"
        subprocess.run([C.FFMPEG, "-y", "-loglevel", "error",
                        "-ss", str(BACKDROP_AT), "-i", str(BACKDROP),
                        "-frames:v", "1", str(wall)], check=True)

        fc = [
            # --- the keep-mask -------------------------------------------
            # tmix over 3 frames takes the jitter out of a per-frame matte;
            # erosion pulls it in a pixel so no cafe fringe survives the cut.
            f"[1:v]scale={W}:{H},format=gray,tmix=frames=3,erosion,"
            f"gblur=sigma=3,split=3[a1][a2][a3]",
            "[2:v]format=gray[below]",
            "[a1][below]blend=all_mode=lighten:shortest=1[alpha]",

            # --- subject --------------------------------------------------
            f"[0:v]fps={FPS},scale={W}:{H},setsar=1,format=yuv420p[src]",
            "[src][alpha]alphamerge[fg]",

            # --- backdrop: marigold wall, barely blurred, plus string lights
            # The backdrop is a STILL. Our camera is locked — differencing the
            # first and last frame is how the table line was trusted in the
            # first place — so a backdrop that pans is a camera that moves in
            # the background and not in the foreground, and the eye catches it
            # immediately. The only motion back there is the bokeh, which is
            # lights, which are allowed to move while the camera does not.
            f"[3:v]scale=1440:2560:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},gblur=sigma={BLUR},"
            "eq=contrast=1.05:saturation=1.25,format=gbrp[bgraw]",
            f"[4:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},setpts=PTS*1.6,format=gbrp[bk]",
            # screen in RGB. In YUV it would push U and V up together and the
            # whole backdrop would go magenta.
            "[bgraw][bk]blend=all_mode=screen:all_opacity=0.38:shortest=1[bgl]",
            "[bgl]split=2[bg1][bg2]",
            "[bg1]format=yuv420p[bg]",
            "[bg][fg]overlay=0:0:shortest=1,format=gbrp[comp]",

            # --- light wrap ------------------------------------------------
            # alpha minus a blurred alpha = a band just INSIDE the subject
            # edge. Screen the backdrop through that band and the subjects
            # pick up the light of the room they are now standing in.
            "[a2]gblur=sigma=11[ablur]",
            "[a3][ablur]blend=all_mode=subtract,eq=contrast=1.5,format=gbrp[edge]",
            "[bg2]gblur=sigma=26[bgsoft]",
            "[bgsoft][edge]blend=all_mode=multiply:shortest=1[wrap]",
            "[comp][wrap]blend=all_mode=screen:all_opacity=0.55:shortest=1,"
            "format=yuv420p[lit]",

            # --- one grade over the lot ------------------------------------
            "[lit]eq=contrast=1.06:saturation=1.12,"
            "colorbalance=rs=0.030:bs=-0.035:rm=0.018:bm=-0.022,"
            "vignette=PI/4.5,unsharp=5:5:0.3:5:5:0[v]",
        ]

        out = OUT / "wedding-scene.mp4"
        cmd = [C.FFMPEG, "-y", "-loglevel", "error",
               "-i", str(SRC),
               "-framerate", str(FPS), "-i", str(masks / "%04d.png"),
               "-loop", "1", "-i", str(below),
               "-loop", "1", "-i", str(wall),
               "-stream_loop", "-1", "-i", str(BOKEH),
               # every -i belongs with the inputs; put this after the output
               # options and ffmpeg reads -map as an input option and bails
               "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
               "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "5:a",
               "-t", f"{_dur(SRC) - 0.1:.2f}", "-shortest",
               "-c:v", "libx264", "-preset", "medium", "-crf", "19",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
               "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, check=True)
        print(f"\n  -> {out}  {_dur(out):.1f}s  {out.stat().st_size / 1e6:.1f}MB")
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    build()
