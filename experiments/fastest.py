#!/usr/bin/env python3
"""One-off: nerdy data-transfer intro, a "get ready" card, then Gaurav's own clip.

    python experiments/fastest.py ~/Downloads/AE8C1753-....MP4

Not part of the daily pipeline — this is an experiment, so it lives here rather
than in make_video.py. It does reuse the pipeline's pieces: Sarvam for the
voice, the Pexels/Commons fetcher for b-roll, and the same 1080x1920 grade.

Structure:
  1. three b-roll beats with narration — the real records for moving data
  2. a card: तैयार हो जाइए / सबसे तेज़ वाला आ रहा है, with the tagline flicker
  3. the supplied clip, untouched apart from scaling to 1080x1920
  4. the brand endcard

The supplied clip has NO audio track, so a silent track is generated for it;
without that, concat drops audio for the whole second half.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # run from anywhere
from pipeline import config as C
from pipeline import fetch, render, tts

W, H, FPS = C.W, C.H, C.FPS
OUT = C.OUTPUT / "experiments"
ACCENT = "&H0000D7FF&"

BEATS = [
    ("आज के दौर में डेटा कितनी तेज़ी से भेजा जा सकता है? 2024 में एक रिकॉर्ड बना — चार सौ दो टेराबिट प्रति सेकंड, और वो भी आम ऑप्टिकल फ़ाइबर पर।",
     {"q": "fiber optic cables glowing", "kind": "video", "must": "fiber"}),
    ("ऊपर आसमान में स्टारलिंक के हज़ारों सैटेलाइट घूम रहे हैं, ताकि इंटरनेट वहाँ भी पहुँचे जहाँ कोई केबल नहीं है।",
     {"q": "satellite orbiting earth animation", "kind": "video", "must": "satellite"}),
    ("और नेटवर्किंग की एक मशहूर लाइन है — टेपों से भरी एक गाड़ी की बैंडविड्थ को कभी कम मत आँकिए।",
     {"q": "server room data centre racks", "kind": "video", "must": "server"}),
]
CARD = ["तैयार हो जाइए", "सबसे तेज़ वाला आ रहा है"]
PUNCH = "न फ़ाइबर, न सैटेलाइट। भारत का सबसे तेज़ डेटा ट्रांसफर — किसी भी फ़ंक्शन में।"
ONSCREEN = ["402 Tb/s", "Starlink", "sneakernet"]


def _dur(p):
    return float(subprocess.run([C.FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], capture_output=True, text=True,
                                check=True).stdout.strip())


def _ass(items, path, end_pad=0.0):
    """Big accent labels at fixed times — no word alignment needed here."""
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n"
            f"WrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
            "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
            "Alignment,MarginL,MarginR,MarginV,Encoding\n"
            f"Style: Big,{C.CAPTION_FONT},150,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,"
            f"1,0,0,0,100,100,0,0,1,8,3,5,0,0,0,1\n"
            f"Style: Label,{C.CAPTION_FONT},92,{ACCENT},{ACCENT},&H00000000,&H64000000,"
            f"1,0,0,0,100,100,0,0,1,6,3,5,0,0,0,1\n\n[Events]\n"
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    body = "".join(
        f"Dialogue: 0,{render._ts(s)},{render._ts(e)},{style},,0,0,0,,{{\\pos({W//2},{y})}}{txt}\n"
        for s, e, txt, style, y in items)
    Path(path).write_text(head + body, encoding="utf-8")


def build(clip_path):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())

    # 1 — narration, one wav per beat so each beat runs exactly as long as its line
    wavs, durs = [], []
    for i, (line, _) in enumerate(BEATS):
        w = tmp / f"vo{i}.wav"
        tts.speak(line, w)
        wavs.append(w); durs.append(_dur(w))
    punch = tmp / "punch.wav"
    tts.speak(PUNCH, punch)

    # 2 — b-roll for the intro
    clips = []
    for i, (_, q) in enumerate(BEATS):
        dest = C.ASSETS / f"fastest-{i}.mp4"
        got = fetch.clip(q["q"], dest, must=q.get("must"), kind=q.get("kind", "video"))
        if not got:
            raise RuntimeError(f"no b-roll for {q['q']!r} — edit the query and rerun")
        clips.append((got, durs[i]))

    # intro voice = the three lines back to back
    vo = tmp / "intro.wav"
    lst = tmp / "vo.txt"
    lst.write_text("\n".join(f"file '{w.resolve()}'" for w in wavs))
    subprocess.run([C.FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(vo)], check=True)

    labels, t = [], 0.0
    for d, txt in zip(durs, ONSCREEN):
        labels.append((t + 0.6, t + d - 0.3, txt, "Label", 1430))
        t += d
    a1 = tmp / "intro.ass"
    _ass(labels, a1)
    intro = tmp / "intro.mp4"
    render.build(clips, vo, a1, intro)

    # 3 — the card, with the same flicker finish.py uses into the tagline
    a2 = tmp / "card.ass"
    _ass([(0.0, 2.6, CARD[0], "Big", 820), (0.55, 2.6, CARD[1], "Big", 1030)], a2)
    card = tmp / "card.mp4"
    subprocess.run([C.FFMPEG, "-y", "-loglevel", "error",
                    "-f", "lavfi", "-i", f"color=c=0x08080c:s={W}x{H}:d=2.6:r={FPS}",
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                    "-shortest", "-vf",
                    f"ass={a2},eq=brightness='if(gt(t,1.9),if(lt(mod(t*16,2),1),0.5,-0.4),0)':eval=frame",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", str(card)], check=True)

    # 4 — the supplied clip: scaled only, plus a silent track and the punch line over its start
    body = tmp / "body.mp4"
    subprocess.run([C.FFMPEG, "-y", "-loglevel", "error", "-i", str(clip_path),
                    "-i", str(punch),
                    "-filter_complex",
                    f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                    f"fps={FPS},setsar=1[v];"
                    f"[1:a]aresample=48000,apad[a]",
                    "-map", "[v]", "-map", "[a]", "-shortest" if False else "-t", f"{_dur(clip_path):.2f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", str(body)], check=True)

    # 5 — endcard, with the one tagline recording
    end = tmp / "end.mp4"
    subprocess.run([C.FFMPEG, "-y", "-loglevel", "error", "-i", str(C.ENDCARD),
                    "-i", str(C.TAGLINE), "-filter_complex",
                    f"[0:v]scale={W}:{H},fps={FPS},setsar=1[v];[1:a]aresample=48000,apad[a]",
                    "-map", "[v]", "-map", "[a]", "-t", f"{_dur(C.ENDCARD):.2f}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", str(end)], check=True)

    # The concat DEMUXER stretched the clip's short voice track across its whole
    # 23s (6s of speech smeared over 18s). The concat FILTER re-times each input,
    # so the clip plays silent as intended.
    parts = (intro, card, body, end)
    out = OUT / "fastest-transfer.mp4"
    cmd = [C.FFMPEG, "-y", "-loglevel", "error"]
    for p_ in parts:
        cmd += ["-i", str(p_)]
    chain = "".join(f"[{i}:v][{i}:a]" for i in range(len(parts)))
    cmd += ["-filter_complex", f"{chain}concat=n={len(parts)}:v=1:a=1[v][a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    print(f"  intro {sum(durs):.1f}s + card 2.6s + clip {_dur(clip_path):.1f}s + endcard "
          f"{_dur(C.ENDCARD):.1f}s\n  -> {out}  {_dur(out):.1f}s")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    build(Path(sys.argv[1]).expanduser())
