"""Sarvam Bulbul TTS. Chunks long scripts, concatenates, writes one WAV per beat."""
import base64, io, json, wave, requests
from . import config as C

def _synth(text: str, speaker: str = None, pace: float = None) -> bytes:
    # Current schema: `text` (a string) + `language_code`. The older shape was
    # `inputs` (a list) + `target_language_code`; if a call 400s, check the docs.
    r = requests.post(
        C.SARVAM_URL,
        headers={"api-subscription-key": C.SARVAM_KEY, "Content-Type": "application/json"},
        json={"text": text, "language_code": C.LANG,
              "speaker": speaker or C.SPEAKER, "model": C.SARVAM_MODEL,
              "pace": pace or C.PACE, "speech_sample_rate": 22050},
        timeout=90,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Sarvam {r.status_code}: {r.text[:400]}")
    return base64.b64decode(r.json()["audios"][0])

def _chunks(text, n):
    out, cur = [], ""
    for part in text.replace("।", "।|").replace("। ", "।|").split("|"):
        if len(cur) + len(part) > n and cur:
            out.append(cur.strip()); cur = part
        else:
            cur += part
    if cur.strip(): out.append(cur.strip())
    return out

def speak(text: str, dest, speaker: str = None, pace: float = None) -> "pathlib.Path":
    """Synthesize text to a mono WAV at dest. Cached by file existence."""
    if dest.exists(): return dest
    parts = [_synth(c, speaker, pace) for c in _chunks(text, C.TTS_CHUNK)]
    frames, params = [], None
    for p in parts:
        with wave.open(io.BytesIO(p)) as w:
            params = params or w.getparams()
            frames.append(w.readframes(w.getnframes()))
    with wave.open(str(dest), "wb") as out:
        out.setparams(params)
        for f in frames: out.writeframes(f)
    return dest
