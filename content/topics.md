# Topic backlog

Added by Gaurav as they come to mind. I research, verify sourceability with
`scout.py`, script, render — and flag honestly when a topic doesn't survive
verification (the way the Amir Khusrau samosa line was cut from 01).

Status: `idea` → `researched` → `scripted` → `rendered` → `approved` → `posted`

| # | Topic | Theme | Status | Notes |
|---|---|---|---|---|
| 07 | why we say "cheers" | everyday-words | **approved** | poison story has no evidence; *chiere* = face |
| 08 | what "Dolby" actually means | everyday-words | **approved** | a surname; first invention was killing tape hiss |
| 09 | ganpati visarjan — the immersion | mythology-and-ritual | **posted** | clay was *designed* to dissolve; POP breaks that logic |
| 10 | who invented the zip | everyday-words | **approved** (rewrite) | Sundback 1913/1917; "zipper" was a boot brand, 1923. ~50 yrs to reach trousers |
| 11 | तेरहवीं — 13 days after death | mythology-and-ritual | **approved** | Garuda Purana puts *sapindikarana* on day **12**, not 13; some observe 12, South India often 16. So 13 is custom, not scripture. **Most sensitive yet** — religious + death. |
| 12 | why every country has its own currency | money-and-trade | **approved** | **Gulf rupee**: RBI issued a separate currency 1959-66 for Bahrain, Kuwait, Muscat & Oman, Qatar, Trucial States. India was the Gulf's central bank. Cause: Indian rupees abroad fuelled gold smuggling home — RBI estimated $92.4m by 1959. |
| 13 | why Ganeshotsav is so big in Maharashtra (Gaurav: "link to Kartikeya?") | mythology-and-ritual | **scripted** | Premise corrected: celebrated in many states; what is Maharashtra's is the *public* festival. Kartikeya race is real text (Shiva Purana, Kumara Khanda ch. 19–20: winner marries first; Skanda leaves "infuriated" for Krauncha) but says nothing about Maharashtra, so it is the hook, not the answer. Answer: Peshwa kuldaivat (Shaniwar Wada) → lost patronage 1818 → public idols 1892 (Rangari) / 1893 (Tilak, Kesari; founder disputed) → state festival 10 Jul 2025. Rejected: Shivaji-era claim (unsourced), "British banned all gatherings" (weak), James Wales 1792 diary (one secondary source). |

## Themes in use

- `kitchen-history` — samosa, chai
- `everyday-words` — shampoo, saanp-seedhi, jobs-seva, cheers, dolby, zip
- `numbers-and-sky` — shunya
- `mythology-and-ritual` — **confirmed by Gaurav 2026-09-13** (visarjan, terahvin)
- `money-and-trade` — **confirmed by Gaurav 2026-09-13** (gulf rupee)

CLAUDE.md says six to eight stories in one theme plus connective narration and a
16:9 re-render becomes a long-form episode. So theme assignment is not cosmetic —
mis-filing fragments a future episode.

## Hook archetype spread

Keep this balanced. `brand/style.md` wants clean coverage before the caption
script bandit starts at ~40 videos.

- `contrarian` — 01, 05, 09
- `delayed_reveal` — 02, 06, 10
- `question` — 03, 07, 08, 11
- `cold_date` — 04, 12

Spread is healthier now. 12-currency was deliberately written as a cold_date
open ("1959। भारत सरकार एक नई करेंसी छापती है — जो भारत में नहीं चलेगी।")
because that archetype had only one entry.


## 10-zip: pulled back for a rewrite (2026-09-14)

Gaurav: "the story line doesn't seem audience sticky and feels loose."
Diagnosis: the strongest fact ("zipper" was a boot brand) lands at 45s; before
it is a march of three inventors and four dates with no stake for the viewer;
the payoff restates the hook instead of landing somewhere new.

Rewrite approved 2026-09-15; `masters/10-zip.mp4` and `output/10-zip/` now hold
the new cut (old one clobbered).

Rewritten 2026-09-14: opens on the boot-name reveal, three inventors in one
beat, payoff on the Talon ad in Esquire's first issue (Autumn 1933). The
"Battle of the Fly" was checked and REJECTED as an unsourced myth.

## Open — needs topics

Backlog is EMPTY as of 2026-09-13. All six month-two topics are scripted.

Bank target is 15 before daily posting starts. Current (2026-09-15):
**6** approved and unposted — 05-shunya, 07-cheers, 08-dolby, 10-zip,
11-terahvin, 12-currency. Posted: 01, 02, 03, 04, 06, 09. **~9 more topics needed.**

05-shunya reminder: post and pin the Oxford 2024 source comment IMMEDIATELY after publishing, before sharing it.

## Known issue: audio fault on 09, 11, 12

Gaurav reported disrupted audio from ~0:35 to the end on 09, and audio issues on
11 and 12. Durations, sample rates and the voice concat all check out clean, so
it is not truncation. Prime suspect is `brand/music/00-drone-placeholder.mp3` —
a synthesised test bed, never chosen, measured as inaudible at -22dB — going
through sidechaincompress plus single-pass loudnorm, whose gain estimate adapts
as the file runs. That would start a fault partway in and hold it to the end.
Drone moved to `brand/music-unused/`; 09 re-rendered without it as the test.

## Opening text (hook_text) — approved by Gaurav 2026-09-15

Burned in by finish.py from frame 0; the cover is the first frame.

| Reel | Opening text |
|---|---|
| 05-shunya | सबसे पुराना शून्य? / वो ख़बर ग़लत थी |
| 07-cheers | Cheers का मतलब / ख़ुशी नहीं है |
| 08-dolby | Dolby का मतलब / क्या होता है? |
| 10-zip | ज़िप का असली नाम / क्या था? |
| 11-terahvin | तेरहवीं / तेरहवें दिन ही क्यों? |
| 12-currency | भारत का पैसा / जो भारत में नहीं चला |

Every future script needs a `hook_text` before render; I propose, Gaurav approves.

