# Reel Factory — हर चीज़ की एक कहानी है

Daily 90-second Hindi origin stories, published to Instagram Reels and YouTube Shorts.

## Start here

```bash
./setup.sh                                        # ffmpeg, fonts, python env
# put three API keys in .env  (all free, links inside .env.example)
./.venv/bin/python make_video.py --check          # verify the machine
./.venv/bin/python make_video.py 01-samosa        # first video
./.venv/bin/python make_video.py --all            # all five
```

Finished MP4s land in `output/`. The caption, hashtags and pinned-comment source
print to the terminal when each render finishes — copy those when you post.

## Post them in this order

1. `01-samosa` — strongest turn, safest claim. Your channel's first impression.
2. `02-shampoo` — delayed reveal, tests a different hook shape.
3. `03-chai` — the most personal one; implicates the viewer's own kitchen.
4. `04-saanp-seedhi` — cold-date opener.
5. `05-shunya` — corrects a story your audience has proudly shared. Expect
   pushback, and post and pin the Oxford 2024 source comment **immediately** after publishing, before sharing — a comment can't exist before the post does.

## What's here

```
content/month-01/scripts/   five scripts as JSON — beats, timings, visual queries,
                            captions, hashtags, sources, and what NOT to claim
pipeline/                   config, Sarvam TTS, whisper alignment, b-roll fetch, render
make_video.py               orchestrator + QC gate
brand/                      fonts, music beds, the fixed end card
assets/                     cache + used-asset ledger (gitignored)
output/                     finished MP4s (gitignored)
.claude/CLAUDE.md           project context for Claude sessions
```

## Three claims to never make

Every food-and-history channel repeats these. None survive checking.

- **Amir Khusrau wrote about samosas c. 1300** — no work, folio or translated line.
- **Dnyaneshwar invented Snakes and Ladders** — one 1871 source, no corroboration.
- **The Bakhshali zero is 3rd century** — Oxford re-dated it to 901–1032 CE in 2024.
  The 2017 version is still live on National Geographic. This is *script 05*.

Each script JSON carries its own `avoid` field. Read it before you record.

## Rules that do not change

- One voice, forever. Audition once, then never touch `SARVAM_SPEAKER`.
- One caption font, forever. Half the visual identity.
- The tag line `हर चीज़ की एक कहानी है` uses the **same audio file** every video.
  Record it once into `brand/tagline.wav`; never let the pipeline regenerate it.
- No video publishes without a source in the pinned comment. Hard rule, not a preference.
