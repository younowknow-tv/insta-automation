"""Central config. Everything tweakable lives here."""
import os, pathlib
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# --- keys (see .env.example) ---
SARVAM_KEY  = os.getenv("SARVAM_API_KEY", "")
PEXELS_KEY  = os.getenv("PEXELS_API_KEY", "")
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY", "")

# --- voice ---
# NOTE: Sarvam's request schema moves between model versions. If a call 400s,
# check https://docs.sarvam.ai and adjust MODEL / SPEAKER / the body in tts.py.
SARVAM_URL   = "https://api.sarvam.ai/text-to-speech"
SARVAM_MODEL = os.getenv("SARVAM_MODEL", "bulbul:v3")
SPEAKER      = os.getenv("SARVAM_SPEAKER", "anushka")   # audition, then never change
LANG         = "hi-IN"
PACE         = float(os.getenv("SARVAM_PACE", "1.0"))   # v3 accepts 0.5–2.0
TTS_CHUNK    = 450          # chars per request; Sarvam caps input length

# --- video ---
W, H, FPS    = 1080, 1920, 30
LUFS         = -14
MUSIC_DB     = -22          # music bed under the VO

# --- captions ---
# macOS ships Kohinoor Devanagari. Noto Sans Devanagari is better — install it
# and change this. Whatever you pick, never change it again: it is half the
# channel's visual identity.
CAPTION_FONT = os.getenv("CAPTION_FONT", "Noto Sans Devanagari")
CAPTION_SIZE = 74
CAPTION_BOLD = 1
PRIMARY      = "&H00FFFFFF"   # white
OUTLINE_COL  = "&H00000000"   # black
OUTLINE_W    = 4
MARGIN_V     = 420            # keeps captions clear of IG/YT chrome
WORDS_PER_CUE = 3

# --- paths ---
SCRIPTS = ROOT / "content" / "month-01" / "scripts"
ASSETS  = ROOT / "assets"
OUTPUT  = ROOT / "output"
BRAND   = ROOT / "brand"
LEDGER  = ASSETS / "used_assets.json"
for p in (ASSETS, OUTPUT, ASSETS / "broll", ASSETS / "voice"):
    p.mkdir(parents=True, exist_ok=True)

# --- instagram publishing (Phase 2) ---
# Instagram Login path: Creator account, no Facebook Page, no App Review.
# Meta does NOT accept file uploads — it cURLs the MP4 from a public HTTPS URL,
# so every publish needs the file hosted somewhere reachable first. See host.py.
IG_APP_ID     = os.getenv("IG_APP_ID", "")
IG_APP_SECRET = os.getenv("IG_APP_SECRET", "")
IG_API        = "https://graph.instagram.com/v25.0"
IG_TOKEN_HOST = "https://graph.instagram.com"      # token exchange/refresh live off-version
IG_TOKEN_FILE = ASSETS / "ig_token.json"
IG_REFRESH_AT = 10          # days left on the 60-day token before we auto-refresh
IG_POLL_EVERY = 5           # seconds between container status checks
IG_POLL_MAX   = 300         # give up on a stuck container after this many seconds

# Where publish.py parks the MP4 so Meta can fetch it. "github" uses a release
# asset on PUBLISH_REPO; "none" means you pass --video-url yourself.
VIDEO_HOST    = os.getenv("VIDEO_HOST", "github")
PUBLISH_REPO  = os.getenv("PUBLISH_REPO", "")      # owner/repo, needs `gh auth login`
PUBLISH_TAG   = os.getenv("PUBLISH_TAG", "reels")  # release the MP4s hang off

# --- binaries ---
# Homebrew's plain `ffmpeg` dropped libass, so it cannot burn in captions at all.
# ffmpeg-full carries libass + HarfBuzz (required for Devanagari conjuncts) but
# installs keg-only, so resolve it by absolute path rather than trusting PATH
# order — a cron runs with a different PATH than an interactive shell.
def _bin(name):
    override = os.getenv(name.upper())
    if override:
        return override
    keg = pathlib.Path(f"/opt/homebrew/opt/ffmpeg-full/bin/{name}")
    return str(keg) if keg.exists() else name

FFMPEG  = _bin("ffmpeg")
FFPROBE = _bin("ffprobe")

# --- brand (fixed forever; see README "Rules that do not change") ---
TAGLINE = BRAND / "tagline.wav"     # the tag line's ONE recording, reused every video
ENDCARD = BRAND / "endcard.mp4"

# --- framing ---
# Stock is mostly landscape. Cropping 16:9 to 9:16 keeps only ~31% of the width,
# which throws away the composition that made the shot worth choosing. So a
# landscape clip is shown whole over a blurred fill of itself; portrait clips
# still fill the frame. Both get a slow push, which the scripts' beat notes ask
# for ("Slow pushes ~4s each").
BLUR_SIGMA   = 40
BLUR_DIM     = -0.12        # darken the fill so the subject stays dominant
ZOOM         = 0.08         # total push over a beat, e.g. 1.00 -> 1.08

# --- shot pacing ---
# The scripts' beat notes assume several shots per beat ("Slow pushes ~4s each",
# "Three quick cuts"). One clip per beat left 32 seconds on a single frame.
SHOT_SECS    = 6.5          # target seconds per shot; a beat may override with "shots"
SHOT_MIN     = 2.2          # never cut faster than this
