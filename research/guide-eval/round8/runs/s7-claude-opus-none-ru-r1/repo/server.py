#!/usr/bin/env python3
"""tricoach backend: sign-in, Intervals.icu OAuth connection, wellness proxy.

Stdlib only. State is in memory (same shape as the prod tables).
"""
import base64, hashlib, hmac, json, os, secrets, threading, time
from http.cookies import SimpleCookie
import urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import config

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
TOKEN_URL = config.INTERVALS_BASE + "/api/oauth/token"
AUTHORIZE_URL = config.INTERVALS_BASE + "/oauth/authorize"
STATE_MAX_AGE = 900        # seconds the user has to finish the consent screen
NONCE_COOKIE = "tc_oauth_nonce"

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
# The state is also bound to the browser that started the flow (nonce in a
# cookie), so an authorize link generated for one account cannot be completed
# in somebody else's browser and attach their Intervals data to that account.
def _state_sig(payload):
    return hmac.new(config.APP_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]


def sign_state(user_id, nonce):
    payload = f"{user_id}:{int(time.time())}:{nonce}"
    return base64.urlsafe_b64encode(f"{payload}:{_state_sig(payload)}".encode()).decode().rstrip("=")


def verify_state(state, nonce, max_age=STATE_MAX_AGE):
    try:
        raw = base64.urlsafe_b64decode((state + "=" * (-len(state) % 4)).encode()).decode()
        user_id, ts, state_nonce, sig = raw.split(":")
        age = time.time() - int(ts)
    except Exception:
        return None
    if not hmac.compare_digest(_state_sig(f"{user_id}:{ts}:{state_nonce}"), sig) or not 0 <= age <= max_age:
        return None
    if not nonce or not hmac.compare_digest(state_nonce, nonce):
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


def missing_scopes(granted):
    """Required scopes the athlete did not grant (WRITE on an area implies READ)."""
    have = {}
    for s in (granted or "").split(","):
        area, _, level = s.strip().partition(":")
        if area:
            have[area] = "WRITE" if "WRITE" in (level, have.get(area)) else level
    missing = []
    for s in config.SCOPES.split(","):
        area, _, level = s.partition(":")
        if area not in have or (level == "WRITE" and have[area] != "WRITE"):
            missing.append(s)
    return missing


def store_connection(user_id, tok):
    # Intervals.icu access tokens are long-lived: the token response has no
    # expires_in and no refresh_token, and the token stays valid until the
    # athlete revokes the app. Only schedule an expiry if the provider gives one.
    expires_in = tok.get("expires_in")
    expires_at = time.time() + int(expires_in) if expires_in else None
    athlete = tok.get("athlete") or {}
    with LOCK:
        CONNECTIONS[user_id] = {
            "athlete_id": athlete.get("id"), "athlete_name": athlete.get("name"),
            "access_token": tok["access_token"], "refresh_token": tok.get("refresh_token"),
            "scope": tok.get("scope"), "expires_at": expires_at, "status": "connected",
        }
    life = f"expires in {expires_in}s" if expires_at else "no expiry"
    log(f"{user_id}: connected as athlete {athlete.get('id')} ({life}, scope {tok.get('scope')})")


def refresh_tokens():
    """Background pass: renew access tokens shortly before they expire."""
    while True:
        time.sleep(config.REFRESH_INTERVAL)
        now = time.time()
        with LOCK:
            for uid, c in CONNECTIONS.items():
                if c["status"] != "connected" or c["expires_at"] is None or c["expires_at"] - now > 300:
                    continue
                if not c["refresh_token"]:
                    log(f"{uid}: token expiry passed and no refresh token on file -> expired, reconnect")
                    c.update(status="expired, reconnect", access_token=None)
                    continue
                try:
                    tok = post_form(TOKEN_URL, {
                        "grant_type": "refresh_token", "refresh_token": c["refresh_token"],
                        "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET,
                    })
                    c.update(access_token=tok["access_token"],
                             refresh_token=tok.get("refresh_token", c["refresh_token"]),
                             expires_at=now + int(tok["expires_in"]) if tok.get("expires_in") else None)
                    log(f"{uid}: token refreshed")
                except Exception as e:
                    log(f"{uid}: refresh failed ({e}) -> expired, reconnect")
                    c.update(status="expired, reconnect", access_token=None)


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

    def redirect(self, url, cookie=None):
        self.send_response(302)
        self.send_header("Location", url)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def cookie(self, name):
        c = SimpleCookie(self.headers.get("Cookie", ""))
        return c[name].value if name in c else None

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
        if url.path == "/api/intervals/callback":
            return self.callback(q)
        if url.path == "/api/intervals/status":
            return self.status()
        if url.path == "/api/intervals/wellness":
            return self.wellness()
        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        url = urllib.parse.urlsplit(self.path)
        if url.path == "/api/intervals/auth/init":
            return self.auth_init()
        if url.path == "/api/intervals/disconnect":
            user = self.require_user()
            if user:
                with LOCK:
                    CONNECTIONS.pop(user["id"], None)
                self.send_json(200, {"ok": True})
            return
        self.send_json(404, {"error": "not found"})

    # Step 1: the SPA calls this with its Bearer token (a plain link navigation
    # cannot carry it), gets the authorize URL back and navigates there itself.
    # The nonce cookie ties the state to this browser.
    def auth_init(self):
        user = self.require_user()
        if not user:
            return
        nonce = secrets.token_urlsafe(16)
        params = {"client_id": config.CLIENT_ID, "redirect_uri": config.REDIRECT_URI,
                  "scope": config.SCOPES, "state": sign_state(user["id"], nonce)}
        body = json.dumps({"url": AUTHORIZE_URL + "?" + urllib.parse.urlencode(params, safe=":,")}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Set-Cookie", f"{NONCE_COOKIE}={nonce}; Path=/api/intervals/callback; "
                                       f"Max-Age={STATE_MAX_AGE}; HttpOnly; SameSite=Lax")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # Step 2: Intervals redirects back here with ?code=&state= (or ?error= if
    # the athlete declined). Top-level GET, so the SameSite=Lax cookie is sent.
    def callback(self, q):
        clear = f"{NONCE_COOKIE}=; Path=/api/intervals/callback; Max-Age=0; HttpOnly; SameSite=Lax"
        if q.get("error"):
            return self.redirect("/?intervals_error=" + urllib.parse.quote(q["error"]), cookie=clear)
        user_id = verify_state(q.get("state", ""), self.cookie(NONCE_COOKIE))
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
        self.redirect("/?connected=1", cookie=clear)

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
            if e.code == 401:   # athlete revoked tricoach on the Intervals side
                with LOCK:
                    c.update(status="revoked, reconnect", access_token=None)
                log(f"{user['id']}: Intervals answered 401 -> revoked, reconnect")
            self.send_json(e.code, {"error": f"intervals returned {e.code}"})
        except Exception as e:
            self.send_json(502, {"error": str(e)})


if __name__ == "__main__":
    threading.Thread(target=refresh_tokens, daemon=True).start()
    log(f"serving on http://localhost:{config.PORT} (intervals: {config.INTERVALS_BASE})")
    ThreadingHTTPServer(("127.0.0.1", config.PORT), Handler).serve_forever()
