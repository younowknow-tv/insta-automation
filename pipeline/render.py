"""ASS captions + FFmpeg assembly. Aspect ratio is a parameter, for long-form later."""
import subprocess, textwrap
from . import config as C

def _dims(path):
    """Source pixel size, so landscape and portrait can be framed differently."""
    out = subprocess.run(
        [C.FFPROBE, "-v", "quiet", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0:s=x", str(path)],
        capture_output=True, text=True).stdout.strip()
    try:
        w, h = out.split("x")[:2]
        return int(w), int(h)
    except ValueError:
        return C.W, C.H


def _ts(t):
    h, r = divmod(max(t, 0), 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"

def ass(words, path, width=C.W, height=C.H):
    """Word-timed caption file. Chunks of WORDS_PER_CUE, pop-in styling."""
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Main,{C.CAPTION_FONT},{C.CAPTION_SIZE},{C.PRIMARY},{C.OUTLINE_COL},&H64000000,{C.CAPTION_BOLD},0,0,0,100,100,0,0,1,{C.OUTLINE_W},2,2,80,80,{C.MARGIN_V},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    lines = []
    groups = [words[i:i + C.WORDS_PER_CUE] for i in range(0, len(words), C.WORDS_PER_CUE)]
    for n, grp in enumerate(groups):
        txt = " ".join(w["w"] for w in grp)
        # the 0.06 tail must never reach the next cue, or libass stacks the two
        end = grp[-1]["end"] + 0.06
        if n + 1 < len(groups):
            end = min(end, groups[n + 1][0]["start"])
        lines.append(f"Dialogue: 0,{_ts(grp[0]['start'])},{_ts(end)},"
                     f"Main,,0,0,0,,{{\\fad(80,80)}}{txt}")
    path.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    return path

def build(clips, voice_wav, ass_path, out_path, music=None,
          width=C.W, height=C.H, duration=None):
    """clips: [(path, seconds)] in order. Crops to fill, concatenates, burns captions."""
    inputs, filters, labels = [], [], []
    for i, (p, dur) in enumerate(clips):
        if str(p).lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            inputs += ["-loop", "1", "-t", f"{dur:.2f}", "-i", str(p)]
        else:
            inputs += ["-stream_loop", "-1", "-t", f"{dur:.2f}", "-i", str(p)]
        w, h = _dims(p)
        if w > h:
            # landscape: show the whole frame over a blurred, dimmed copy of itself
            pre = (f"[{i}:v]split=2[bg{i}][fg{i}];"
                   f"[bg{i}]scale={width}:{height}:force_original_aspect_ratio=increase,"
                   f"crop={width}:{height},gblur=sigma={C.BLUR_SIGMA},"
                   f"eq=brightness={C.BLUR_DIM}[b{i}];"
                   f"[fg{i}]scale={width}:-2[f{i}];"
                   f"[b{i}][f{i}]overlay=(W-w)/2:(H-h)/2,")
        else:
            pre = (f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
                   f"crop={width}:{height},")
        # slow push; the increment is sized so the beat ends at exactly 1+ZOOM
        inc = C.ZOOM / max(dur * C.FPS, 1)
        filters.append(
            pre + f"fps={C.FPS},setsar=1,"
            f"zoompan=z='min(zoom+{inc:.6f},{1 + C.ZOOM})':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={C.FPS},"
            f"eq=saturation=0.92:contrast=1.06:gamma=0.98[v{i}]")
        labels.append(f"[v{i}]")
    vi = len(clips)
    inputs += ["-i", str(voice_wav)]
    if music:
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        # the voice feeds TWO filters — the sidechain key and the final mix — so
        # it has to be split. An ffmpeg pad can only ever be consumed once.
        amix = (f"[{vi}:a]aresample=48000,asplit=2[vo1][vo2];"
                f"[{vi+1}:a]aresample=48000,volume={C.MUSIC_DB}dB[bg];"
                f"[bg][vo1]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=250[duck];"
                f"[duck][vo2]amix=inputs=2:duration=first:dropout_transition=0[aout]")
        aout = "[aout]"
    else:
        amix = f"[{vi}:a]aresample=48000[vo]"
        aout = "[vo]"
    # loudnorm has to live INSIDE the complex graph: ffmpeg refuses -af on a
    # stream that comes out of filter_complex ("simple and complex filtering
    # cannot be used together for the same stream").
    chain = ";".join(filters) + ";" + "".join(labels) + \
            f"concat=n={len(clips)}:v=1:a=0[cat];" + \
            f"[cat]ass={ass_path}[vout];" + amix + \
            f";{aout}loudnorm=I={C.LUFS}:TP=-1.5:LRA=11[anorm]"
    aout = "[anorm]"
    cmd = [C.FFMPEG, "-y", *inputs, "-filter_complex", chain,
           "-map", "[vout]", "-map", aout,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", str(C.FPS),
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart"]
    if duration: cmd += ["-t", f"{duration:.2f}"]
    cmd.append(str(out_path))
    subprocess.run(cmd, check=True)
    return out_path
