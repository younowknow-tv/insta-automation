"""Hard gates on a finished MP4. Shared by the renderer and the publisher."""
import json, subprocess
from pathlib import Path
from . import config as C


def qc(path: Path):
    """Hard fails, in the order they are cheapest to check. -> (dur, mb, fails)"""
    p = json.loads(subprocess.run(
        [C.FFPROBE, "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", str(path)],
        capture_output=True, text=True).stdout)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    dur, mb = float(p["format"]["duration"]), int(p["format"]["size"]) / 1e6
    fails = []
    if not (30 <= dur <= 95):              fails.append(f"duration {dur:.1f}s outside 30–95")
    if (v["width"], v["height"]) != (C.W, C.H): fails.append(f"{v['width']}x{v['height']} not 1080x1920")
    if v["codec_name"] != "h264":          fails.append(f"codec {v['codec_name']} not h264")
    if mb > 100:                           fails.append(f"{mb:.0f}MB over the 100MB cap")
    if not any(s["codec_type"] == "audio" for s in p["streams"]): fails.append("no audio track")
    return dur, mb, fails
