# Brand constants

Decide each of these **once**. Changing any of them later costs recognition,
which is the only thing that compounds.

| | Value | Locked? |
|---|---|---|
| Voice | Sarvam `bulbul:v3`, speaker set in `.env` | audition first |
| Caption font | Noto Sans Devanagari, 74px, bold, white on black outline | |
| Caption position | 420px from bottom — clears IG and YT chrome | yes |
| Grade | saturation 0.92, contrast 1.06, gamma 0.98 | in `render.py` |
| Loudness | −14 LUFS, TP −1.5 | yes |
| Tag line | हर चीज़ की एक कहानी है — one recorded file, reused | yes |
| Safe area | keep text inside 80px L/R margins | yes |

## Caption script: Devanagari or Hinglish?

Not decided. Both are defensible: Devanagari respects the material, romanized
Hinglish often reads faster at phone size. This is a bandit dimension, not an
opinion — run it once ~40 videos of baseline exist. Whichever wins, freeze it.

## Music

Drop commercially-cleared MP3s into `brand/music/`. The renderer picks the first
alphabetically and ducks it under the voice. Keep a licence note per track — a
"free" track with an attribution clause is a claim waiting to happen.
