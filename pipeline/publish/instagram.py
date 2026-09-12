"""Instagram Reels publishing. Container -> poll -> publish -> source comment.

Instagram Login path (Creator account, no Facebook Page, no App Review), per the
settled decision in CLAUDE.md. Meta renders the video server-side, so the
container is not publishable the instant it is created — hence the poll.
"""
import time, requests
from .. import config as C


def _call(method, path, token, **params):
    r = requests.request(method, f"{C.IG_API}/{path}",
                         params={**params, "access_token": token}, timeout=90)
    if r.status_code != 200:
        raise RuntimeError(f"IG {method} {path} -> {r.status_code}: {r.text[:400]}")
    return r.json()


def quota(token, uid):
    """-> posts used in the trailing 24h. Cap is 100; we use one a day."""
    d = _call("GET", f"{uid}/content_publishing_limit", token,
              fields="config,quota_usage")
    return d["data"][0].get("quota_usage", 0)


def container(token, uid, video_url, caption):
    d = _call("POST", f"{uid}/media", token,
              media_type="REELS", video_url=video_url, caption=caption)
    print(f"  container {d['id']}")
    return d["id"]


def wait(token, cid):
    """Block until Meta finishes transcoding. Raises on ERROR/EXPIRED."""
    waited = 0
    while waited < C.IG_POLL_MAX:
        d = _call("GET", cid, token, fields="status_code,status")
        st = d.get("status_code")
        if st == "FINISHED":
            print(f"  container ready after {waited}s")
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {st}: {d.get('status', '')[:300]}")
        time.sleep(C.IG_POLL_EVERY)
        waited += C.IG_POLL_EVERY
    raise RuntimeError(f"container stuck at IN_PROGRESS after {C.IG_POLL_MAX}s")


def publish(token, uid, cid):
    d = _call("POST", f"{uid}/media_publish", token, creation_id=cid)
    return d["id"]


def comment(token, media_id, message):
    """Posts the source. NOTE: the API cannot pin — that stays a manual step."""
    d = _call("POST", f"{media_id}/comments", token, message=message)
    return d["id"]


def permalink(token, media_id):
    return _call("GET", media_id, token, fields="permalink").get("permalink", "")
