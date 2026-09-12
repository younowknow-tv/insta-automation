"""Word timings for captions.

Whisper is used for TIMING ONLY. Its Hindi transcription is not reliable enough
to put on screen — on the first render it turned समोसा into "समोँ सा", जिस चीज़
into "जस चीस" and सबसे ज़्यादा into "सबसी ज़ाद". We already know the exact words:
they are in the script. So we align the script's characters against the ASR's
characters and borrow the timings, which keeps the sync while guaranteeing the
text on screen is the text that was written and fact-checked.
"""
import difflib, re
from faster_whisper import WhisperModel

_model = None
_DEV = re.compile(r"[^ऀ-ॿ]")


def words(wav_path):
    """Raw ASR output -> [{'w':str,'start':float,'end':float}, ...]"""
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = _model.transcribe(str(wav_path), language="hi", word_timestamps=True,
                                vad_filter=False, beam_size=5)
    out = []
    for s in segs:
        for w in (s.words or []):
            out.append({"w": w.word.strip(), "start": w.start, "end": w.end})
    return out


def _char_times(asr):
    """Flatten ASR words to Devanagari chars, each carrying an interpolated time."""
    chars, times = [], []
    for x in asr:
        c = _DEV.sub("", x["w"])
        if not c:
            continue
        span = (x["end"] - x["start"]) / len(c)
        for k, ch in enumerate(c):
            chars.append(ch)
            times.append((x["start"] + k * span, x["start"] + (k + 1) * span))
    return "".join(chars), times


def script_words(wav_path, line, duration):
    """-> [{'w': <script word>, 'start': float, 'end': float}, ...]

    Falls back to spreading the line evenly across `duration` if ASR gives us
    nothing usable, so a caption track always exists.
    """
    tokens = [t for t in line.split() if _DEV.sub("", t)]
    if not tokens:
        return []

    asr_chars, asr_times = _char_times(words(wav_path))

    # where each token's characters sit in the stripped script string
    spans, pos = [], 0
    for t in tokens:
        c = _DEV.sub("", t)
        spans.append((pos, pos + len(c)))
        pos += len(c)
    script_chars = "".join(_DEV.sub("", t) for t in tokens)

    got = [None] * len(tokens)
    if asr_chars:
        # script char index -> asr char index, for the parts that agree
        m = {}
        for i, j, n in difflib.SequenceMatcher(
                None, script_chars, asr_chars, autojunk=False).get_matching_blocks():
            for k in range(n):
                m[i + k] = j + k
        for idx, (a, b) in enumerate(spans):
            hit = [m[i] for i in range(a, b) if i in m]
            if hit:
                got[idx] = (asr_times[min(hit)][0], asr_times[max(hit)][1])

    # interpolate whatever did not align, then clamp to a sane monotonic track
    known = [i for i, g in enumerate(got) if g]
    if not known:
        step = duration / len(tokens)
        return [{"w": t, "start": i * step, "end": (i + 1) * step}
                for i, t in enumerate(tokens)]
    for i in range(len(tokens)):
        if got[i]:
            continue
        lo = max([k for k in known if k < i], default=None)
        hi = min([k for k in known if k > i], default=None)
        a = got[lo][1] if lo is not None else 0.0
        b = got[hi][0] if hi is not None else duration
        gap = [k for k in range(len(tokens)) if not got[k]
               and (lo is None or k > lo) and (hi is None or k < hi)]
        n = max(len(gap), 1)
        r = gap.index(i) if i in gap else 0
        got[i] = (a + (b - a) * r / n, a + (b - a) * (r + 1) / n)

    out, prev = [], 0.0
    for t, (s, e) in zip(tokens, got):
        s = max(s, prev)
        e = max(e, s + 0.08)
        out.append({"w": t, "start": s, "end": e})
        prev = s
    return out
