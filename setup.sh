#!/usr/bin/env bash
set -e
echo "→ ffmpeg + fontconfig"
command -v brew >/dev/null || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
# Homebrew's plain `ffmpeg` dropped libass — it cannot burn in captions at all.
# ffmpeg-full carries libass/harfbuzz/freetype and is keg-only, so config.py
# points at it by absolute path rather than trusting PATH order.
brew list ffmpeg-full >/dev/null 2>&1 || brew install ffmpeg-full
brew list fontconfig  >/dev/null 2>&1 || brew install fontconfig
echo "→ Noto Sans Devanagari"
brew list --cask font-noto-sans-devanagari >/dev/null 2>&1 || \
  brew install --cask font-noto-sans-devanagari || \
  echo "  (skip — falls back to Kohinoor Devanagari; set CAPTION_FONT in .env)"
echo "→ python env"
python3 -m venv .venv
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r pipeline/requirements.txt
[ -f .env ] || cp .env.example .env
echo
echo "Done. Now:"
echo "  1. put your three API keys in .env"
echo "  2. ./.venv/bin/python make_video.py --check"
echo "  3. ./.venv/bin/python make_video.py 01-samosa"
