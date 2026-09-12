"""Instagram long-lived token store.

The token lasts 60 days and dies silently — the same trap the YouTube consent
screen sets at 7 days. So we persist the expiry alongside the token and refresh
it whenever a publish runs with less than IG_REFRESH_AT days left. A daily cron
therefore keeps the token alive forever without anyone thinking about it.
"""
import json, time, datetime as dt, requests
from .. import config as C


def _save(token, user_id, expires_in):
    C.IG_TOKEN_FILE.write_text(json.dumps({
        "token": token,
        "user_id": user_id,
        "expires": (dt.datetime.now(dt.timezone.utc)
                    + dt.timedelta(seconds=int(expires_in))).isoformat(),
    }, indent=1))


def _load():
    if not C.IG_TOKEN_FILE.exists():
        raise RuntimeError(
            "No Instagram token yet. Run:  python publish.py --login <short-lived-token>\n"
            "  (get one from the Instagram app dashboard -> API setup with Instagram login)")
    return json.loads(C.IG_TOKEN_FILE.read_text())


def days_left(store=None) -> float:
    store = store or _load()
    exp = dt.datetime.fromisoformat(store["expires"])
    return (exp - dt.datetime.now(dt.timezone.utc)).total_seconds() / 86400


def _me(tok):
    r = requests.get(f"{C.IG_API}/me",
                     params={"fields": "user_id,username", "access_token": tok}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"/me {r.status_code}: {r.text[:400]}")
    return r.json()


def _exchange(short_lived):
    """-> (token, expires_in) or None if Meta says it is not a short-lived token."""
    r = requests.get(f"{C.IG_TOKEN_HOST}/access_token",
                     params={"grant_type": "ig_exchange_token",
                             "client_secret": C.IG_APP_SECRET,
                             "access_token": short_lived}, timeout=30)
    if r.status_code == 200:
        d = r.json()
        return d["access_token"], d.get("expires_in", 5184000)
    return None


def bootstrap(tok: str):
    """Store a working 60-day token.

    The dashboard's "Generate token" button already hands out a long-lived token
    for the Instagram Login path, and re-exchanging one is an error. So try the
    exchange, and if Meta rejects it, verify the token as-is and keep it.
    """
    if not C.IG_APP_SECRET:
        raise RuntimeError("IG_APP_SECRET missing — see .env.example")
    got = _exchange(tok)
    if got:
        tok, expires = got
        print("  exchanged short-lived token for a 60-day one")
    else:
        expires = 5184000
        print("  token is already long-lived; storing as-is")
    who = _me(tok)          # raises if the token is genuinely bad
    _save(tok, who.get("user_id") or who["id"], expires)
    return who.get("username", "?")


def _refresh(store):
    """Meta refuses a refresh on a token under 24h old; that's fine, it has 60 days."""
    r = requests.get(f"{C.IG_TOKEN_HOST}/refresh_access_token",
                     params={"grant_type": "ig_refresh_token",
                             "access_token": store["token"]}, timeout=30)
    if r.status_code != 200:
        print(f"  !! token refresh {r.status_code}: {r.text[:200]}")
        return store
    d = r.json()
    _save(d["access_token"], store["user_id"], d.get("expires_in", 5184000))
    print(f"  token refreshed — {days_left():.0f} days left")
    return _load()


def current():
    """-> (token, ig_user_id), refreshing first if the token is close to dying."""
    store = _load()
    left = days_left(store)
    if left <= 0:
        raise RuntimeError("Instagram token expired. Re-run --login with a fresh "
                           "short-lived token from the dashboard.")
    if left < C.IG_REFRESH_AT:
        store = _refresh(store)
    return store["token"], store["user_id"]
