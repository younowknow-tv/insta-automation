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
| Wedding scene swap | `wedding_scene.py` + `PersonMask.swift` | **built 2026-11-28, not posted.** `IMG_8076.MOV` — two people eating in a cafe, put in front of a marigold wall. |
| World's fastest data transfer | `fastest.py` | built 2026-11-10, never posted. Three open points were never settled: silence over Gaurav's clip, trimming its dull first ~5s, and consent for the identifiable people in it. |

## wedding_scene.py — how far the matte goes

Mattes come from Apple's Vision framework via `PersonMask.swift`, compiled on
first run. Local, no model download, ~40s for 297 frames.

The limit worth knowing before asking for more of these: a person matte marks
people and nothing else. Subjects who are **eating** come with a table, and
cutting on the person matte alone floats them in mid-air with their hands over
nothing. This clip works because the camera is locked, so the table could be
held in with a static half-plane. **A handheld clip would need the table
tracked, which is a different and much larger job.**

What that leaves: the chairs are below the line too, and replacing them sits
the woman on thin air — so everything below the table stays as shot, and the
new venue can only appear in the band above it. In this framing the subjects
fill ~85% of frame, so that band is thin. It is why the backdrop is a flower
wall and not a wedding hall: a hall, a stage and a banquet room were all tried
and all read as "a warm blurry room" at that size. Marigolds read even as a
sliver.

**For the next one of these: leave room around the subjects when shooting.**
Space is what makes a scene swap possible; there is no recovering it later.

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
