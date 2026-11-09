#!/usr/bin/env python3
"""Drive the full tricoach <-> Intervals.icu flow against the local fake.

Steps mirror what the SPA + browser do, including the parts a browser
navigation cannot do (sending the bearer token).
"""
import json, os, subprocess, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRI = "http://127.0.0.1:8766"
LOG = os.path.join(ROOT, ".e2e", "tricoach.log")
FAILURES = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not cond:
        FAILURES.append(name)


def get(url, token=None, follow=True):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, dict(r.headers), r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()


def get_no_follow(url, token=None):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    opener = urllib.request.build_opener(NoRedirect())
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with opener.open(req, timeout=10) as r:
            return r.status, dict(r.headers), r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()


def wait_port(port, proc):
    for _ in range(100):
        if proc.poll() is not None:
            raise RuntimeError(f"server on port {port} exited early")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1):
                return
        except urllib.error.HTTPError:
            return  # any HTTP answer means the server is up
        except Exception:
            time.sleep(0.1)
    raise RuntimeError(f"server on port {port} did not start")


fake = subprocess.Popen([sys.executable, os.path.join(ROOT, ".e2e", "fake_intervals.py")])
env = dict(os.environ, INTERVALS_BASE="http://127.0.0.1:8899")
logf = open(LOG, "w")
tri = subprocess.Popen([sys.executable, os.path.join(ROOT, "server.py")], env=env, stdout=logf, stderr=subprocess.STDOUT)
try:
    wait_port(8899, fake)
    wait_port(8766, tri)

    # 1. signed-in athlete, as the SPA sees it
    code, _, body = get(TRI + "/api/me", "tok-okafor")
    check("sign-in works", code == 200 and json.loads(body)["name"] == "C. Okafor", body)

    # 2. Connect click: fetch carries the bearer token, server returns the URL
    code, _, body = get(TRI + "/api/intervals/auth/init", "tok-okafor")
    url = json.loads(body).get("url", "")
    check("auth/init returns authorize URL", code == 200 and url.startswith("http://127.0.0.1:8899/oauth/authorize?"), body)

    # 3. the URL must ask only for registered scopes and be RFC-shaped
    q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
    scopes = set(filter(None, q.get("scope", "").split(",")))
    check("no unregistered CALENDAR scopes", "CALENDAR:READ" not in scopes and "CALENDAR:WRITE" not in scopes, q.get("scope", ""))
    check("response_type=code sent", q.get("response_type") == "code")

    # 4. prove the old scope list is what Intervals rejects (captured behavior)
    bad = dict(q, scope="ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE")
    bad_url = "http://127.0.0.1:8899/oauth/authorize?" + urllib.parse.urlencode(bad, safe=":,")
    code, _, body = get_no_follow(bad_url)
    check("old scope list -> 400 invalid_request (reproduces log)", code == 400 and json.loads(body).get("error") == "invalid_request", body)

    # 5. browser navigates to the authorize URL (no auth header involved)
    code, hdrs, _ = get_no_follow(url)
    loc = hdrs.get("Location", "")
    check("authorize redirects to callback with code+state",
          code == 302 and loc.startswith("http://localhost:8766/api/intervals/callback?code=") and "state=" in loc, loc)

    # 6. callback: exchange code, store connection, land back on the SPA
    code, hdrs, _ = get_no_follow(loc)
    check("callback completes, redirects to /?connected=1", code == 302 and hdrs.get("Location") == "/?connected=1", str(hdrs))

    # 7. status + wellness for the connected athlete
    code, _, body = get(TRI + "/api/intervals/status", "tok-okafor")
    st = json.loads(body)
    check("status: connected", code == 200 and st.get("connected") is True and st.get("athlete", {}).get("id") == "i12345", body)
    code, _, body = get(TRI + "/api/intervals/wellness", "tok-okafor")
    check("wellness proxy works", code == 200 and isinstance(json.loads(body), list), body)

    # 8. the one that got away: stay connected well past the old 3600s kill
    print("waiting 70s so the refresher thread runs a full pass...")
    time.sleep(70)
    code, _, body = get(TRI + "/api/intervals/status", "tok-okafor")
    check("still connected after refresher pass (no spurious expiry)",
          code == 200 and json.loads(body).get("connected") is True, body)
finally:
    tri.terminate()
    fake.terminate()
    logf.close()

logtext = open(LOG).read()
check("server logged non-expiring token", "token does not expire" in logtext)
check("no 'expired, reconnect' for the healthy connection", "expired, reconnect" not in logtext)

print()
if FAILURES:
    print("FAILURES:", ", ".join(FAILURES))
    sys.exit(1)
print("ALL CHECKS PASSED")
