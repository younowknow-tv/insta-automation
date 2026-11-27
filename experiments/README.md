# Experiments

One-off builds that are not part of the daily pipeline. They reuse the
pipeline's pieces (config, fetch, render, tts) but have their own shot lists
and their own rules, so they live here rather than in `make_video.py`.

Renders go to `output/experiments/`, which is **gitignored and local only**.
This repo is public, so nothing here is uploaded to a Release: putting an
unposted video in a Release on a public repo makes it publicly downloadable,
which is not the same as backing it up privately. Ask before pushing any of
these anywhere.

| Build | Script | State |
|---|---|---|
| ASMR kadhi-chawal | `asmr_food.py` | **approved 2026-11-24, held — do not post.** For a NEW channel, not now_you_know.tv. Unbranded; `CHANNEL = ""` until the channel is named. |
| World's fastest data transfer | `fastest.py` | built 2026-11-10, never posted. Three open points were never settled: silence over Gaurav's clip, trimming its dull first ~5s, and consent for the identifiable people in it. |

## asmr_food.py — source clips

The render reads four files straight out of `~/Downloads` and **nothing in this
repo holds a copy**:

| File | What it is |
|---|---|
| `IMG_7804.MOV` | 4K, 49s — the pot, the chilli tadka, the ladle, plating |
| `IMG_7805.MOV` | 4K, 8s — the thecha going on |
| `IMG_7806.MOV` | 4K, 24s — the finished plate (**first 13s only**; after that a child is eating, face in frame, deliberately unused) |
| `IMG_8003.MOV` | 1080, 12m11s — eating, one fixed overhead angle |

Clear Downloads and the reel cannot be rebuilt or re-cut. The finished MP4
would survive, but every further change — a new title, a different grade, a
longer hold — needs the sources. Move them somewhere durable before cleaning
up, or accept the current cut as final.

The two grades in that script are tuned **against each other**, not
separately: the 4K clips and the eating clip have to match across a cut. If
either is changed, check the seam at the join (around 0:15) before shipping.
