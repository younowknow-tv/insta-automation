"""Park the MP4 at a public HTTPS URL, because Meta will not accept an upload.

Instagram cURLs the file off a URL you hand it, so the video has to be publicly
reachable for the ~minute the fetch takes. GitHub release assets are free, need
no new account, and sit in the same place the Phase 2 cron will already be
running. Swap in R2/S3 by writing another function with this signature.
"""
import json, subprocess, shutil, requests
from .. import config as C


def _gh(*args):
    if not shutil.which("gh"):
        raise RuntimeError("gh CLI missing — brew install gh && gh auth login")
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _reachable(url):
    """Meta gets a 404 from a private repo just like anyone else. Check first."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=30)
        return r.status_code == 200
    except requests.RequestException:
        return False


def github_release(mp4):
    """Upload mp4 as a release asset on PUBLISH_REPO. -> public URL."""
    if not C.PUBLISH_REPO:
        raise RuntimeError("PUBLISH_REPO not set (owner/repo) — see .env.example")
    repo, tag = C.PUBLISH_REPO, C.PUBLISH_TAG

    code, _, _ = _gh("release", "view", tag, "--repo", repo)
    if code != 0:
        print(f"  creating release '{tag}' on {repo}")
        _gh("release", "create", tag, "--repo", repo, "--title", tag,
            "--notes", "Video assets for API publishing. Not a software release.")

    print(f"  uploading {mp4.name} -> {repo} ({tag})")
    code, _, err = _gh("release", "upload", tag, str(mp4), "--repo", repo, "--clobber")
    if code != 0:
        raise RuntimeError(f"gh release upload failed: {err[:300]}")

    code, out, err = _gh("release", "view", tag, "--repo", repo, "--json", "assets")
    if code != 0:
        raise RuntimeError(f"gh release view failed: {err[:300]}")
    for a in json.loads(out)["assets"]:
        if a["name"] == mp4.name:
            url = a["url"]
            if not _reachable(url):
                raise RuntimeError(
                    f"{url}\n  is not publicly reachable — Instagram will fail the same way.\n"
                    f"  Is {repo} private? The release asset must be public.")
            print(f"  hosted {url}")
            return url
    raise RuntimeError(f"uploaded but no asset named {mp4.name} came back")


def public_url(mp4):
    if C.VIDEO_HOST == "github":
        return github_release(mp4)
    raise RuntimeError(f"VIDEO_HOST={C.VIDEO_HOST!r} has no uploader; pass --video-url instead")
