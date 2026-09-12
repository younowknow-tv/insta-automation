#!/usr/bin/env python3
"""
Reel Factory v0 — one script JSON in, one QC-passed MP4 out.

    python make_video.py 01-samosa
    python make_video.py --all
    python make_video.py --check          # verify ffmpeg / fonts / keys only

Everything runs locally except Sarvam TTS and the stock-clip APIs.
"""
import argparse, json, subprocess, sys, shutil
from pathlib import Path
from pipeline import config as C, tts, align, fetch, render
from pipeline.qc import qc


def check():
    ok = True
    ff = shutil.which(C.FFMPEG)
    print(f"ffmpeg            {ff or 'MISSING — brew install ffmpeg'}")
    ok &= bool(ff)
    if ff:
        cfg = subprocess.run([C.FFMPEG, "-version"], capture_output=True, text=True).stdout
        for lib in ("libass", "libharfbuzz", "libfreetype"):
            here = lib in cfg
            print(f"  {lib:14s}  {'yes' if here else 'NO — Devanagari will break'}")
            ok &= here
    fonts = subprocess.run(["fc-list"], capture_output=True, text=True).stdout \
        if shutil.which("fc-list") else ""
    if fonts:
        print(f"font '{C.CAPTION_FONT}'  {'found' if C.CAPTION_FONT in fonts else 'NOT FOUND'}")
    else:
        print(f"font '{C.CAPTION_FONT}'  (install fontconfig to verify: brew install fontconfig)")
    # Pixabay is only the fallback when Pexels has no unused clip for a query,
    # so a missing key costs coverage, not the render.
    for name, key, required in (("SARVAM", C.SARVAM_KEY, True),
                                ("PEXELS", C.PEXELS_KEY, True),
                                ("PIXABAY", C.PIXABAY_KEY, False)):
        miss = "MISSING — see .env.example" if required else "absent — fallback only, fewer b-roll options"
        print(f"{name+'_API_KEY':18s}{'set' if key else miss}")
        if required: ok &= bool(key)
    # brand assets: not hard failures (the pipeline degrades), but silent
    # substitutions are worse than a warning, so name them.
    music = sorted((C.BRAND / "music").glob("*.mp3")) if (C.BRAND / "music").exists() else []
    print(f"{'tagline.wav':18s}" + ("found — reused, never regenerated"
          if C.TAGLINE.exists() else "absent — will be recorded on the first render"))
    print(f"{'endcard.mp4':18s}" + ("found" if C.ENDCARD.exists()
          else "ABSENT — the tag beat will reuse the previous clip instead"))
    print(f"{'music bed':18s}" + (f"{len(music)} track(s)" if music else "none — renders without music"))

    print("\n" + ("ready" if ok else "not ready — fix the lines above"))
    return ok


# bulbul:v3 female voices, the register the channel was written for.
# Full list is in Sarvam's docs; pass --audition a,b,c to try others.
AUDITION_VOICES = ["shreya", "ritu", "priya", "neha", "kavya", "suhani"]


def audition(voices=None):
    """Render the tag line in several voices so it can be chosen ONCE.

    The first real render freezes brand/tagline.wav forever, so this is the
    moment to decide. Costs a few hundred characters of Sarvam credit.
    """
    line = json.loads(next(iter(sorted(C.SCRIPTS.glob("*.json")))).read_text())
    tag = next(b["line"] for b in line["beats"] if b["mode"] == "FIXED")
    out = C.OUTPUT / "audition"; out.mkdir(parents=True, exist_ok=True)
    print(f'auditioning: "{tag}"\n')
    for v in (voices or AUDITION_VOICES):
        dest = out / f"{v}.wav"
        try:
            tts.speak(tag, dest, speaker=v)
            print(f"  {v:10s} {dest}")
        except Exception as e:
            print(f"  {v:10s} FAILED — {str(e)[:120]}")
    print(f"\nListen, then set SARVAM_SPEAKER in .env. After the first render "
          f"the choice is permanent.")
    return out


def build_one(sid: str):
    spec = json.loads((C.SCRIPTS / f"{sid}.json").read_text())
    print(f"\n=== {spec['id']}  ({spec['hook_archetype']}) ===")
    vdir = C.ASSETS / "voice" / sid; vdir.mkdir(parents=True, exist_ok=True)

    # 1. voice, per beat, so a beat's length sets its own visual duration
    beats, clips, all_words, t0 = spec["beats"], [], [], 0.0
    for i, b in enumerate(beats):
        if b["mode"] == "FIXED":
            # One recording of the tag line, forever — half the channel's identity.
            # Synthesized once on the first video, then never regenerated.
            if not C.TAGLINE.exists():
                tts.speak(b["line"], C.TAGLINE)
                print(f"  recorded {C.TAGLINE.name} — permanent from now on")
            wav = C.TAGLINE
        else:
            wav = tts.speak(b["line"], vdir / f"{i:02d}.wav")
        dur = float(subprocess.run(
            [C.FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(wav)], capture_output=True, text=True).stdout.strip())
        if b["mode"] != "FIXED":
            # captions carry the SCRIPT's words, timed by ASR — never ASR's words
            w = align.script_words(wav, b["line"], dur)
            for x in w: all_words.append({**x, "start": x["start"] + t0, "end": x["end"] + t0})
        b["_wav"], b["_dur"], t0 = wav, dur, t0 + dur
        print(f"  beat {b['n']:<8} {dur:5.1f}s")

    # 2. one voice track
    voice = vdir / "voice.wav"
    lst = vdir / "concat.txt"
    lst.write_text("\n".join(f"file '{b['_wav'].resolve()}'" for b in beats))
    subprocess.run([C.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(voice)], check=True, capture_output=True)

    # 3. visuals — a long beat becomes several shots, per its own note
    for i, b in enumerate(beats):
        if b["mode"] == "FIXED" or not b.get("query"):
            src = C.ENDCARD
            if not src.exists(): src = clips[-1][0] if clips else None
            if src is None:
                print(f"  !! beat {i} has no visual"); return None
            clips.append((src, b["_dur"]))
            continue

        # a beat may pin specific local files — your own footage always beats stock
        own = [C.ROOT / f for f in (b.get("files") or ([b["file"]] if b.get("file") else []))]
        missing = [f for f in own if not f.exists()]
        if missing:
            print("  !! missing pinned shot(s): " + ", ".join(str(m) for m in missing))
            return None

        n = b.get("shots") or max(1, round(b["_dur"] / C.SHOT_SECS))
        n = max(1, min(n, int(b["_dur"] // C.SHOT_MIN) or 1))
        queries = b.get("queries") or [b["query"]]
        got = list(own)
        for k in range(max(0, n - len(own))):
            # a query may be a plain string, or {"q":..., "must":...} when that
            # shot has its own subject — one beat-level `must` cannot cover a
            # beat that moves from potatoes to samosas.
            item = queries[k % len(queries)]
            if isinstance(item, dict) and item.get("file"):
                # own footage, in its place in the running order
                src = C.ROOT / item["file"]
                if not src.exists():
                    print(f"  !! pinned shot missing: {src}"); return None
                print(f"  b-roll {'own footage':<20} {item['file']}")
                got.append(src)
                continue
            q    = item["q"] if isinstance(item, dict) else item
            must = item.get("must") if isinstance(item, dict) else b.get("must")
            kind = item.get("kind") if isinstance(item, dict) else None
            dest = C.ASSETS / "broll" / f"{sid}-{i:02d}-{k:02d}.mp4"
            src = fetch.clip(q, dest, must, kind or b.get("kind", "video"))
            if src: got.append(src)
        if not got:
            print(f"  !! beat {i} has no visual — fix the query in the JSON and rerun")
            return None
        if len(got) < n:
            print(f"     beat {i}: wanted {n} shots, found {len(got)}")
        share = b["_dur"] / len(got)
        print(f"  beat {b['n']:<8} {len(got)} shot(s) x {share:.1f}s")
        for src in got:
            clips.append((src, share))

    # 4. captions + render
    ap = render.ass(all_words, C.ASSETS / f"{sid}.ass")
    music = next(iter(sorted((C.BRAND / "music").glob("*.mp3"))), None) \
        if (C.BRAND / "music").exists() else None
    out = C.OUTPUT / f"{sid}.mp4"
    render.build(clips, voice, ap, out, music=music)

    dur, mb, fails = qc(out)
    print(f"  -> {out.name}  {dur:.1f}s  {mb:.1f}MB  " +
          ("PASS" if not fails else "FAIL: " + "; ".join(fails)))
    print(f"\n  caption: {spec['caption']}")
    print(f"  tags:    {' '.join(spec['hashtags'])}")
    print(f"  pin:     {spec['pinned_comment']}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("script_id", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--audition", nargs="?", const="", metavar="v1,v2",
                    help="render the tag line in several voices, then stop")
    a = ap.parse_args()
    if a.check: sys.exit(0 if check() else 1)
    if a.audition is not None:
        audition([v.strip() for v in a.audition.split(",") if v.strip()] or None)
        sys.exit(0)
    if not check(): sys.exit(1)
    ids = sorted(p.stem for p in C.SCRIPTS.glob("*.json")) if a.all else [a.script_id]
    if not ids or ids == [None]: ap.error("give a script id or --all")
    for i in ids: build_one(i)
