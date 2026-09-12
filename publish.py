#!/usr/bin/env python3
"""Reel Factory — publish a rendered MP4 to Instagram Reels.

    python publish.py --login <short-lived-token>   # once, then never again
    python publish.py --check                       # verify creds + quota
    python publish.py 01-samosa --dry-run           # host + build container, stop
    python publish.py 01-samosa                     # publish for real

Renders come from make_video.py; this only ships what is already in output/.
"""
import argparse, json, sys, datetime as dt
from pathlib import Path
from pipeline import config as C
from pipeline.publish import token as T, host, instagram as ig
from pipeline.qc import qc

LEDGER = C.ASSETS / "published.json"
CAPTION_MAX = 2200
COMMENT_MAX = 2200


def _ledger():
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else {}


def _record(sid, **row):
    l = _ledger(); l[sid] = row; LEDGER.write_text(json.dumps(l, indent=1, ensure_ascii=False))


def caption_for(spec):
    body = spec["caption"].strip()
    tags = " ".join(spec.get("hashtags", []))
    full = f"{body}\n\n{tags}".strip()
    if len(full) > CAPTION_MAX:
        raise RuntimeError(f"caption {len(full)} chars, over Instagram's {CAPTION_MAX}")
    return full


PROVIDERS = {"pexels": "Pexels", "pixabay": "Pixabay"}


def broll_credit(sid):
    """Credit only the stock providers this video actually used.

    Pexels' API guidelines ask for credit where practical. The channel already
    pins its sources, so the b-roll line rides along in the same comment.
    """
    if not C.LEDGER.exists():
        return ""
    assets = json.loads(C.LEDGER.read_text()).get("assets", {})
    used = {uid.split(":")[0] for f, uid in assets.items() if f.startswith(f"{sid}-")}
    names = [PROVIDERS[p] for p in sorted(used) if p in PROVIDERS]
    return f"B-roll: {' · '.join(names)}" if names else ""


def source_comment(sid, spec):
    """The pinned comment: the story's sources, then the b-roll credit."""
    body = spec["pinned_comment"].strip()
    credit = broll_credit(sid)
    full = f"{body}\n\n{credit}" if credit else body
    if len(full) > COMMENT_MAX:
        raise RuntimeError(f"source comment {len(full)} chars, over Instagram's {COMMENT_MAX}")
    return full


def preflight(sid):
    """Hard gates. Everything that can fail cheaply fails here, before any upload."""
    spec_path = C.SCRIPTS / f"{sid}.json"
    if not spec_path.exists():
        raise RuntimeError(f"no script {spec_path}")
    spec = json.loads(spec_path.read_text())

    # The non-negotiable from CLAUDE.md: no source, no publish.
    if not spec.get("pinned_comment", "").strip():
        raise RuntimeError(f"{sid} has no pinned_comment — hard QC fail, not publishing")

    mp4 = C.OUTPUT / f"{sid}.mp4"
    if not mp4.exists():
        raise RuntimeError(f"{mp4} missing — run: python make_video.py {sid}")
    dur, mb, fails = qc(mp4)
    if fails:
        raise RuntimeError(f"{sid} fails QC: {'; '.join(fails)}")

    if sid in _ledger():
        raise RuntimeError(f"{sid} already published ({_ledger()[sid]['at']}) — "
                           f"delete its row from {LEDGER.name} to force a repost")
    print(f"  QC pass  {dur:.1f}s  {mb:.1f}MB")
    return spec, mp4


def check():
    ok = True
    for name, val in (("IG_APP_ID", C.IG_APP_ID), ("IG_APP_SECRET", C.IG_APP_SECRET)):
        print(f"{name:16s}{'set' if val else 'MISSING — see .env.example'}")
        ok &= bool(val)
    try:
        tok, uid = T.current()
        print(f"{'token':16s}ok, {T.days_left():.0f} days left  (user {uid})")
        print(f"{'quota':16s}{ig.quota(tok, uid)} posts used of 100 in the last 24h")
    except Exception as e:
        print(f"{'token':16s}{e}")
        ok = False
    if C.VIDEO_HOST == "github":
        print(f"{'PUBLISH_REPO':16s}{C.PUBLISH_REPO or 'MISSING — needed for VIDEO_HOST=github'}")
        ok &= bool(C.PUBLISH_REPO)
    print("\n" + ("ready to publish" if ok else "not ready — fix the lines above"))
    return ok


def publish_one(sid, dry=False, video_url=None):
    print(f"\n=== publishing {sid} ===")
    spec, mp4 = preflight(sid)
    tok, uid = T.current()
    cap = caption_for(spec)

    url = video_url or host.public_url(mp4)
    cid = ig.container(tok, uid, url, cap)
    ig.wait(tok, cid)

    if dry:
        print("  --dry-run: container built and ready, stopping before publish")
        return None

    media_id = ig.publish(tok, uid, cid)
    link = ig.permalink(tok, media_id)
    print(f"  published {media_id}  {link}")

    src = source_comment(sid, spec)
    cmt = ig.comment(tok, media_id, src)
    print(f"  source comment {cmt}")

    _record(sid, media_id=media_id, permalink=link, comment_id=cmt,
            at=dt.datetime.now(dt.timezone.utc).isoformat(), pinned=False)

    # The API has no pin endpoint. This is the one step a human still owes.
    print(f"\n  ACTION REQUIRED — pin the source comment by hand:\n    {link}\n"
          f"    comment: {src[:90]}{'...' if len(src) > 90 else ''}")
    return media_id


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("script_id", nargs="?")
    ap.add_argument("--login", metavar="SHORT_LIVED_TOKEN")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--video-url", help="skip hosting, use this public URL")
    a = ap.parse_args()

    if a.login:
        print(f"logged in as @{T.bootstrap(a.login)} — token good for 60 days, "
              f"auto-refreshed on every publish")
        sys.exit(0)
    if a.check:
        sys.exit(0 if check() else 1)
    if not a.script_id:
        ap.error("give a script id, --login, or --check")
    try:
        publish_one(a.script_id, dry=a.dry_run, video_url=a.video_url)
    except Exception as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
