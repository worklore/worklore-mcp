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
STATE_COOKIE = "tc_oauth_state"

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


def expiry_from(tok, now):
    # Intervals.icu access tokens do not expire: the token response carries no
    # expires_in and no refresh_token. Only schedule an expiry when the provider
    # actually gives one; otherwise the token is valid until the athlete revokes
    # it (which we notice as a 401 from the API).
    exp = tok.get("expires_in")
    return now + int(exp) if exp else None


def store_connection(user_id, tok):
    expires_at = expiry_from(tok, time.time())
    refresh = tok.get("refresh_token")
    athlete = tok.get("athlete") or {}
    with LOCK:
        CONNECTIONS[user_id] = {
            "athlete_id": athlete.get("id"), "athlete_name": athlete.get("name"),
            "access_token": tok["access_token"], "refresh_token": refresh,
            "scope": tok.get("scope"), "expires_at": expires_at, "status": "connected",
        }
    life = "no expiry" if expires_at is None else f"expires in {int(expires_at - time.time())}s"
    log(f"{user_id}: connected as athlete {athlete.get('id')} ({life})")


def refresh_tokens():
    """Background pass: renew access tokens shortly before they expire.

    Only applies to tokens the provider gave an expiry for; Intervals.icu tokens
    normally have none and are left alone.
    """
    while True:
        time.sleep(config.REFRESH_INTERVAL)
        now = time.time()
        with LOCK:
            due = [(uid, c["refresh_token"], c["expires_at"]) for uid, c in CONNECTIONS.items()
                   if c["status"] == "connected" and c["expires_at"] is not None
                   and c["expires_at"] - now <= 300]
        for uid, refresh, expires_at in due:
            if not refresh:
                if expires_at > now:
                    continue   # nothing to renew with; keep using it until it actually expires
                log(f"{uid}: token expired and no refresh token on file -> expired, reconnect")
                mark_expired(uid)
                continue
            try:
                tok = post_form(TOKEN_URL, {
                    "grant_type": "refresh_token", "refresh_token": refresh,
                    "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET,
                })
            except Exception as e:
                log(f"{uid}: refresh failed ({e}) -> expired, reconnect")
                mark_expired(uid)
                continue
            with LOCK:
                c = CONNECTIONS.get(uid)
                if c:
                    c.update(access_token=tok["access_token"],
                             refresh_token=tok.get("refresh_token", refresh),
                             expires_at=expiry_from(tok, time.time()))
            log(f"{uid}: token refreshed")


def mark_expired(uid):
    with LOCK:
        c = CONNECTIONS.get(uid)
        if c:
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

    def redirect(self, url, headers=()):
        self.send_response(302)
        self.send_header("Location", url)
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()

    def cookie(self, name):
        for part in self.headers.get("Cookie", "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == name:
                return v
        return None

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

    # Step 1: build the authorize URL. The SPA calls this with fetch (a plain
    # link navigation cannot carry the Bearer token) and then sends the browser
    # to the returned URL. The state is also pinned to this browser in a cookie
    # so a callback carrying someone else's state is rejected.
    def auth_init(self):
        user = self.require_user()
        if not user:
            return
        state = sign_state(user["id"])
        params = {"client_id": config.CLIENT_ID, "redirect_uri": config.REDIRECT_URI,
                  "scope": config.SCOPES, "state": state}
        body = json.dumps({"url": AUTHORIZE_URL + "?" + urllib.parse.urlencode(params, safe=":,")}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Set-Cookie", f"{STATE_COOKIE}={state}; Path=/api/intervals/callback; "
                                       "Max-Age=900; HttpOnly; SameSite=Lax")
        self.end_headers()
        self.wfile.write(body)

    # Step 2: Intervals redirects back here with ?code=&state=.
    def callback(self, q):
        if q.get("error"):
            log(f"authorize returned error: {q.get('error')} {q.get('error_description', '')}")
            return self.redirect("/?connect_error=" + urllib.parse.quote(q["error"]))
        state = q.get("state", "")
        user_id = verify_state(state)
        pinned = self.cookie(STATE_COOKIE)
        if not user_id or not q.get("code") or not pinned or not hmac.compare_digest(pinned, state):
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
        self.redirect("/?connected=1", [("Set-Cookie", f"{STATE_COOKIE}=; Path=/api/intervals/callback; Max-Age=0")])

    def status(self):
        user = self.require_user()
        if not user:
            return
        with LOCK:
            c = CONNECTIONS.get(user["id"])
        if not c or c["status"] != "connected":
            return self.send_json(200, {"connected": False, "status": c["status"] if c else "disconnected"})
        self.send_json(200, {"connected": True, "status": "connected", "scope": c["scope"],
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
            if e.code == 401:   # token revoked on the Intervals side
                log(f"{user['id']}: intervals returned 401 -> expired, reconnect")
                mark_expired(user["id"])
            self.send_json(e.code, {"error": f"intervals returned {e.code}"})
        except Exception as e:
            self.send_json(502, {"error": str(e)})


if __name__ == "__main__":
    threading.Thread(target=refresh_tokens, daemon=True).start()
    log(f"serving on http://localhost:{config.PORT} (intervals: {config.INTERVALS_BASE})")
    ThreadingHTTPServer(("127.0.0.1", config.PORT), Handler).serve_forever()
