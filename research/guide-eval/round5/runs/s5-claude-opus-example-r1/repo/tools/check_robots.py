"""Evaluate robots.txt the way Google does: longest matching rule wins, Allow wins ties.
Usage: python3 -I tools/check_robots.py site/robots.txt"""
import re, sys

def rules(path):
    out = []
    for line in open(path):
        line = line.split("#", 1)[0].strip()
        k, _, v = line.partition(":")
        if k.strip().lower() in ("allow", "disallow") and v.strip():
            out.append((k.strip().lower() == "allow", v.strip()))
    return out

def matches(pattern, url):
    rx = re.escape(pattern).replace(r"\*", ".*")
    if rx.endswith(r"\$"):
        rx = rx[:-2] + "$"
    return re.match(rx, url) is not None

def allowed(rs, url):
    best = None  # (length, allow)
    for allow, pat in rs:
        if matches(pat, url):
            cand = (len(pat), allow)
            if best is None or cand > best:
                best = cand
    return True if best is None else best[1]

CASES = {
    "/": True, "/n/drip-line-pressure": True, "/app.js": True, "/styles.css": True,
    "/v1/notes?limit=50": True, "/v1/notes/drip-line-pressure": True,
    "/v1/notes/drip-line-pressure/reactions": False,
    "/v1/me": False, "/v1/me/drafts": False, "/v1/auth/token": False,
    "/admin/": False, "/v1/anything-else": False,
}
rs = rules(sys.argv[1])
bad = 0
for url, want in CASES.items():
    got = allowed(rs, url)
    bad += got != want
    print(f"{'ok ' if got == want else 'BAD'} {'allow' if got else 'block'}  {url}")
sys.exit(1 if bad else 0)
