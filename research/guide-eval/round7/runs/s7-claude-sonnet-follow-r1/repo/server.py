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
# user_id -> {athlete_id, athlete_name, access_token, scope, status}
CONNECTIONS = {}
LOCK = threading.Lock()


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "[intervals]", msg, flush=True)


# --- state parameter: HS256 JWT carrying the user through the redirect ------
def _b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _jwt_sig(signing_input):
    return _b64(hmac.new(config.APP_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest())


def sign_state(user_id, ttl=900):
    head = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64(json.dumps({"sub": user_id, "purpose": "intervals_oauth",
                            "exp": int(time.time()) + ttl}).encode())
    return f"{head}.{body}.{_jwt_sig(head + '.' + body)}"


def verify_state(state):
    try:
        head, body, sig = state.split(".")
        if json.loads(_unb64(head)).get("alg") != "HS256":
            return None
        if not hmac.compare_digest(_jwt_sig(head + "." + body), sig):
            return None
        claims = json.loads(_unb64(body))
        if claims.get("purpose") != "intervals_oauth" or time.time() > claims["exp"]:
            return None
        return claims["sub"]
    except Exception:
        return None


# --- Intervals.icu calls ----------------------------------------------------
def post_form(url, fields):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def exchange_code(code):
    return post_form(TOKEN_URL, {
        "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": code,
    })


class AccountMismatch(Exception):
    pass


def store_connection(user_id, tok):
    """Intervals tokens never expire and have no refresh_token; they die only on revocation."""
    athlete = tok.get("athlete") or {}
    with LOCK:
        old = CONNECTIONS.get(user_id)
        if old and old.get("athlete_id") and old["athlete_id"] != athlete.get("id"):
            raise AccountMismatch(f"stored {old['athlete_id']}, got {athlete.get('id')}")
        # NOTE: perpetual credential - encrypt at rest in the real store.
        CONNECTIONS[user_id] = {
            "athlete_id": athlete.get("id"), "athlete_name": athlete.get("name"),
            "access_token": tok["access_token"], "scope": tok.get("scope"), "status": "connected",
        }
    log(f"{user_id}: connected as athlete {athlete.get('id')}")


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

    # Step 1 (authenticated POST/XHR): return the authorize URL for the SPA to navigate to.
    def auth_init(self):
        user = self.require_user()
        if not user:
            return
        params = {"client_id": config.CLIENT_ID, "redirect_uri": config.REDIRECT_URI,
                  "scope": config.SCOPES, "state": sign_state(user["id"])}
        self.send_json(200, {"authorize_url": AUTHORIZE_URL + "?" + urllib.parse.urlencode(params, safe=":,")})

    # Step 2: Intervals redirects back here with ?code=&state=.
    def callback(self, q):
        user_id = verify_state(q.get("state", ""))
        if not user_id or not q.get("code"):
            return self.send_json(400, {"error": "bad state or code"})
        try:
            tok = exchange_code(q["code"])
            store_connection(user_id, tok)
        except AccountMismatch as e:
            log(f"{user_id}: reconnect rejected, account mismatch ({e})")
            return self.send_json(409, {"error": "different Intervals.icu account than the one connected"})
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
            if e.code == 401:  # revoked: clear token, prompt reconnect
                with LOCK:
                    c.update(status="expired, reconnect", access_token=None)
            self.send_json(e.code, {"error": f"intervals returned {e.code}"})
        except Exception as e:
            self.send_json(502, {"error": str(e)})


if __name__ == "__main__":
    log(f"serving on http://localhost:{config.PORT} (intervals: {config.INTERVALS_BASE})")
    ThreadingHTTPServer(("127.0.0.1", config.PORT), Handler).serve_forever()
