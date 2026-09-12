# Project context

Faceless Hindi channel: 90-second origin stories ("हर चीज़ की एक कहानी है"),
topics spanning mythology, food and science under one promise — *this everyday
thing has a surprising origin*. Target audience Indian.

## Settled decisions — do not relitigate without being asked

- **Platforms:** Instagram Reels + YouTube Shorts, same MP4, from day one.
  Tune against YouTube (richer retention data, lower variance); Instagram is
  distribution we do not experiment on.
- **Instagram API:** Instagram Login path — Creator account, **no Facebook Page**,
  **no App Review** (Standard Access covers an account holding a role on our own app).
- **YouTube:** OAuth consent screen must be **In production**. Left in Testing,
  refresh tokens expire every 7 days and the pipeline dies silently each week.
- **Voice:** Sarvam Bulbul v3, ~₹3/video. Kokoro's Hindi and ElevenLabs' Hindi
  both lag Indian-first prosody. One speaker, forever.
- **Visuals:** branch on `visual_mode` per beat. ANCIENT → generated stills
  (stock stands in for now); MODERN → stock b-roll. Stock libraries have almost
  nothing usable for mythology, which is why the branch exists.
- **Goal:** the daily short is top-of-funnel. Indian Shorts RPM is ₹1–2 per 1,000
  views, so ad revenue is a rounding error. The destination is a long-form Hindi
  channel at ~50× the RPM. Hence `theme` on every story — six to eight stories
  per theme, plus connective narration and a 16:9 re-render, is an episode.
  **Never hard-code 9:16.**
- **Tuning:** Thompson sampling over 3–4 discrete arms, one dimension at a time,
  reviewed weekly, switched on only after ~40 posts. Hook archetype first.
  The decision stays in code; the LLM writes language, never conclusions.

## Non-negotiables

- Every video ships with a real source in the pinned comment. Hard QC fail otherwise.
- Religious material is framed as art and text history, never as verdict.
- Verify Devanagari conjunct shaping (क्ष, त्र, ज्ञ) on any render-path change —
  libass without HarfBuzz turns them into glyph soup.

## Current state

Month one written (five scripts fact-checked to source, 25 further angles in
four themes). Pipeline is v0: runs locally, publishes nothing yet. Phase 2
(YouTube + Instagram publish clients, GitHub Actions daily cron) not started.
