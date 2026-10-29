#!/usr/bin/env python3
"""tricoach backend: sign-in, Intervals.icu OAuth connection, wellness proxy.

Stdlib only. State is in memory (same shape as the prod tables).
"""
import base64, hashlib, hmac, json, os, threading, time
import urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import config

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
TOKEN_URL = config.INTERVALS_BASE + "/api/oauth/token"
AUTHORIZE_URL = config.INTERVALS_BASE + "/oauth/authorize"

# --- in-memory store -------------------------------------------------------
USERS = {
    "tok-okafor": {"id": "u_okafor", "name": "C. Okafor"},
    "tok-rivera": {"id": "u_rivera", "name": "T. Rivera"},
}
# user_id -> {athlete_id, athlete_name, access_token, refresh_token, scope, expires_at, status}
CONNECTIONS = {}
LOCK = threading.Lock()


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "[intervals]", msg, flush=True)


# --- state parameter: carries the user through the redirect -----------------
def sign_state(user_id):
    payload = f"{user_id}:{int(time.time())}"
    sig = hmac.new(config.APP_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode()


def verify_state(state, max_age=900):
    try:
        user_id, ts, sig = base64.urlsafe_b64decode(state.encode()).decode().split(":")
    except Exception:
        return None
    payload = f"{user_id}:{ts}"
    good = hmac.new(config.APP_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(good, sig) or time.time() - int(ts) > max_age:
        return None
    return user_id


# --- Intervals.icu calls ----------------------------------------------------
def post_form(url, fields):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def exchange_code(code):
    return post_form(TOKEN_URL, {
        "grant_type": "authorization_code", "client_id": config.CLIENT_ID,
        "client_secret": config.CLIENT_SECRET, "code": code, "redirect_uri": config.REDIRECT_URI,
    })


def expiry_from(tok):
    """Absolute expiry time, or None if the provider did not give one.

    Intervals.icu access tokens do not expire (they live until the athlete
    revokes the app) and come without expires_in / refresh_token, so a missing
    expires_in means "no expiry", not "assume one hour".
    """
    return time.time() + int(tok["expires_in"]) if tok.get("expires_in") else None


def missing_scopes(granted):
    """Requested areas the token does not cover (WRITE covers READ)."""
    have = {}
    for s in (granted or "").split(","):
        area, _, level = s.strip().partition(":")
        if area:
            have[area] = "WRITE" if "WRITE" in (level, have.get(area)) else level
    out = []
    for s in config.SCOPES.split(","):
        area, _, level = s.partition(":")
        if have.get(area) != "WRITE" and have.get(area) != level:
            out.append(s)
    return out


def store_connection(user_id, tok):
    expires_at = expiry_from(tok)
    athlete = tok.get("athlete") or {}
    with LOCK:
        CONNECTIONS[user_id] = {
            "athlete_id": athlete.get("id"), "athlete_name": athlete.get("name"),
            "access_token": tok["access_token"], "refresh_token": tok.get("refresh_token"),
            "scope": tok.get("scope"), "expires_at": expires_at, "status": "connected",
        }
    life = "no expiry" if expires_at is None else f"expires in {int(expires_at - time.time())}s"
    log(f"{user_id}: connected as athlete {athlete.get('id')} ({life}, scope {tok.get('scope')})")


def refresh_tokens():
    """Background pass: renew access tokens shortly before they expire."""
    while True:
        time.sleep(config.REFRESH_INTERVAL)
        now = time.time()
        with LOCK:
            due = [(uid, dict(c)) for uid, c in CONNECTIONS.items()
                   if c["status"] == "connected" and c["expires_at"] is not None
                   and c["expires_at"] - now <= 300]
        for uid, c in due:
            if not c["refresh_token"]:
                if c["expires_at"] > now:
                    continue          # still valid; nothing we can do until it actually expires
                log(f"{uid}: token expired and no refresh token on file -> expired, reconnect")
                update = dict(status="expired, reconnect", access_token=None)
            else:
                try:
                    tok = post_form(TOKEN_URL, {
                        "grant_type": "refresh_token", "refresh_token": c["refresh_token"],
                        "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET,
                    })
                    update = dict(access_token=tok["access_token"],
                                  refresh_token=tok.get("refresh_token", c["refresh_token"]),
                                  expires_at=expiry_from(tok))
                    log(f"{uid}: token refreshed")
                except Exception as e:
                    log(f"{uid}: refresh failed ({e}) -> expired, reconnect")
                    update = dict(status="expired, reconnect", access_token=None)
            with LOCK:
                cur = CONNECTIONS.get(uid)
                # skip if the athlete reconnected/disconnected while we were talking to Intervals
                if cur is not None and cur["access_token"] == c["access_token"]:
                    cur.update(update)


def intervals_get(conn, path):
    req = urllib.request.Request(f"{config.INTERVALS_BASE}/api/v1/athlete/{conn['athlete_id']}{path}",
                                 headers={"Authorization": "Bearer " + conn["access_token"]})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, json.loads(r.read().decode())


# --- HTTP ---------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(time.strftime("%Y-%m-%d %H:%M:%S"), "[http]", fmt % args, flush=True)

    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, name, ctype):
        p = os.path.join(STATIC, name)
        if not os.path.isfile(p):
            return self.send_json(404, {"error": "not found"})
        with open(p, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, url):
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()

    def current_user(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        return USERS.get(auth[7:].strip())

    def require_user(self):
        user = self.current_user()
        if user is None:
            self.log_message("%s %s 401 (no Authorization header)", self.command, self.path)
            self.send_json(401, {"error": "unauthorized"})
        return user

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        q = dict(urllib.parse.parse_qsl(url.query))
        if url.path == "/":
            return self.send_file("index.html", "text/html; charset=utf-8")
        if url.path.startswith("/static/"):
            return self.send_file(os.path.basename(url.path), "application/javascript" if url.path.endswith(".js") else "text/plain")
        if url.path == "/api/me":
            user = self.require_user()
            return user and self.send_json(200, user)
        if url.path == "/api/intervals/auth/init":
            return self.auth_init()
        if url.path == "/api/intervals/callback":
            return self.callback(q)
        if url.path == "/api/intervals/status":
            return self.status()
        if url.path == "/api/intervals/wellness":
            return self.wellness()
        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        url = urllib.parse.urlsplit(self.path)
        if url.path == "/api/intervals/disconnect":
            user = self.require_user()
            if user:
                with LOCK:
                    CONNECTIONS.pop(user["id"], None)
                self.send_json(200, {"ok": True})
            return
        self.send_json(404, {"error": "not found"})

    # Step 1: build the authorize URL for the signed-in user. The SPA calls
    # this with fetch (so the Bearer token is sent) and then navigates the
    # browser to the returned URL; a plain link would carry no Authorization
    # header and a 302 would be followed cross-origin by fetch itself.
    def auth_init(self):
        user = self.require_user()
        if not user:
            return
        params = {"client_id": config.CLIENT_ID, "redirect_uri": config.REDIRECT_URI,
                  "scope": config.SCOPES, "state": sign_state(user["id"])}
        self.send_json(200, {"url": AUTHORIZE_URL + "?" + urllib.parse.urlencode(params, safe=":,")})

    # Step 2: Intervals redirects back here with ?code=&state=.
    def callback(self, q):
        if q.get("error"):              # athlete declined, or Intervals rejected the request
            log(f"authorize returned error: {q.get('error')} {q.get('error_description', '')}")
            return self.redirect("/?intervals_error=" + urllib.parse.quote(q["error"]))
        user_id = verify_state(q.get("state", ""))
        if not user_id or not q.get("code"):
            return self.send_json(400, {"error": "bad state or code"})
        try:
            tok = exchange_code(q["code"])
            store_connection(user_id, tok)
        except urllib.error.HTTPError as e:
            log(f"{user_id}: token exchange failed: HTTP {e.code} {e.read()[:200]!r}")
            return self.send_json(502, {"error": "token exchange failed"})
        except Exception as e:
            log(f"{user_id}: token exchange failed: {e}")
            return self.send_json(502, {"error": "token exchange failed"})
        self.redirect("/?connected=1")

    def status(self):
        user = self.require_user()
        if not user:
            return
        with LOCK:
            c = CONNECTIONS.get(user["id"])
        if not c or c["status"] != "connected":
            return self.send_json(200, {"connected": False, "status": c["status"] if c else "disconnected"})
        self.send_json(200, {"connected": True, "status": "connected", "scope": c["scope"],
                             "missing_scopes": missing_scopes(c["scope"]),
                             "athlete": {"id": c["athlete_id"], "name": c["athlete_name"]}})

    def wellness(self):
        user = self.require_user()
        if not user:
            return
        with LOCK:
            c = CONNECTIONS.get(user["id"])
        if not c or c["status"] != "connected":
            return self.send_json(409, {"error": "intervals not connected"})
        try:
            code, data = intervals_get(c, "/wellness")
            self.send_json(code, data)
        except urllib.error.HTTPError as e:
            if e.code == 401:           # the token really is dead (athlete revoked the app)
                log(f"{user['id']}: intervals rejected the token -> expired, reconnect")
                with LOCK:
                    if CONNECTIONS.get(user["id"]) is c:
                        c.update(status="expired, reconnect", access_token=None)
            self.send_json(e.code, {"error": f"intervals returned {e.code}"})
        except Exception as e:
            self.send_json(502, {"error": str(e)})


if __name__ == "__main__":
    threading.Thread(target=refresh_tokens, daemon=True).start()
    log(f"serving on http://localhost:{config.PORT} (intervals: {config.INTERVALS_BASE})")
    ThreadingHTTPServer(("127.0.0.1", config.PORT), Handler).serve_forever()
