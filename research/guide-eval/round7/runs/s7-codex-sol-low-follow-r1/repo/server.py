#!/usr/bin/env python3
"""tricoach backend: sign-in, Intervals.icu OAuth connection, wellness proxy.

State is in memory (same shape as the prod tables).
"""
import base64, hashlib, hmac, json, os, threading, time
import urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from cryptography.fernet import Fernet

import config

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
TOKEN_URL = config.INTERVALS_BASE + "/api/oauth/token"
AUTHORIZE_URL = config.INTERVALS_BASE + "/oauth/authorize"
TOKEN_CIPHER = Fernet(base64.urlsafe_b64encode(hashlib.sha256(config.APP_SECRET.encode()).digest()))

# --- in-memory store -------------------------------------------------------
USERS = {
    "tok-okafor": {"id": "u_okafor", "name": "C. Okafor"},
    "tok-rivera": {"id": "u_rivera", "name": "T. Rivera"},
}
# user_id -> {athlete_id, athlete_name, encrypted_token, scope, status}
CONNECTIONS = {}
LOCK = threading.Lock()


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "[intervals]", msg, flush=True)


# --- state parameter: carries the user through the redirect -----------------
def sign_state(user_id):
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b'=').decode()
    payload = base64.urlsafe_b64encode(json.dumps({"sub": user_id, "purpose": "intervals_oauth",
        "exp": int(time.time()) + 900}, separators=(",", ":")).encode()).rstrip(b'=').decode()
    signed = f"{header}.{payload}"
    sig = base64.urlsafe_b64encode(hmac.new(config.APP_SECRET.encode(), signed.encode(), hashlib.sha256).digest()).rstrip(b'=').decode()
    return f"{signed}.{sig}"


def verify_state(state):
    try:
        header, payload, sig = state.split(".")
        signed = f"{header}.{payload}"
        good = base64.urlsafe_b64encode(hmac.new(config.APP_SECRET.encode(), signed.encode(), hashlib.sha256).digest()).rstrip(b'=').decode()
        if not hmac.compare_digest(good, sig):
            return None
        h = json.loads(base64.urlsafe_b64decode(header + "=" * (-len(header) % 4)))
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if h != {"alg": "HS256", "typ": "JWT"} or claims.get("purpose") != "intervals_oauth":
            return None
        if not isinstance(claims.get("exp"), int) or not time.time() < claims["exp"] <= time.time() + 900:
            return None
        return claims["sub"] if claims.get("sub") in {u["id"] for u in USERS.values()} else None
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


def store_connection(user_id, tok):
    athlete = tok.get("athlete") or {}
    if not athlete.get("id") or not tok.get("access_token"):
        raise ValueError("incomplete token response")
    with LOCK:
        prior = CONNECTIONS.get(user_id)
        if prior and prior["athlete_id"] != athlete["id"]:
            raise ValueError("Intervals athlete does not match existing connection")
        CONNECTIONS[user_id] = {
            "athlete_id": athlete.get("id"), "athlete_name": athlete.get("name"),
            "encrypted_token": TOKEN_CIPHER.encrypt(tok["access_token"].encode()),
            "scope": tok.get("scope"), "status": "connected",
        }
    log(f"{user_id}: connected as athlete {athlete.get('id')}")


def intervals_get(conn, path):
    req = urllib.request.Request(f"{config.INTERVALS_BASE}/api/v1/athlete/{conn['athlete_id']}{path}",
                                 headers={"Authorization": "Bearer " + TOKEN_CIPHER.decrypt(conn["encrypted_token"]).decode()})
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

    # Step 1: authenticated fetch returns the authorize URL to the SPA.
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
        except urllib.error.HTTPError as e:
            log(f"{user_id}: token exchange failed: HTTP {e.code} {e.read()[:200]!r}")
            return self.send_json(502, {"error": "token exchange failed"})
        except ValueError as e:
            return self.send_json(409, {"error": str(e)})
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
            if e.code == 401:
                with LOCK:
                    current = CONNECTIONS.get(user["id"])
                    if current is c:
                        current.update(status="reconnect", encrypted_token=None)
                return self.send_json(409, {"error": "Intervals.icu disconnected; reconnect your account"})
            self.send_json(e.code, {"error": f"intervals returned {e.code}"})
        except Exception as e:
            self.send_json(502, {"error": str(e)})


if __name__ == "__main__":
    log(f"serving on http://localhost:{config.PORT} (intervals: {config.INTERVALS_BASE})")
    ThreadingHTTPServer(("127.0.0.1", config.PORT), Handler).serve_forever()
