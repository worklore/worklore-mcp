"""Drive tricoach through connect -> callback -> status -> wellness against a local mock of Intervals.icu.

Run: python3 flow_test.py  (starts server.py and the mock itself; both on localhost)
"""
import json, os, subprocess, sys, threading, time, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

APP = os.path.dirname(os.path.abspath(__file__))
MOCK_PORT = 9999
MOCK = f"http://127.0.0.1:{MOCK_PORT}"
PORT = 8790  # 8766 is in use by another server on this machine
APP_URL = f"http://127.0.0.1:{PORT}"
# Same as server.py's __main__, but with the test port applied to config before serving.
WRAPPER = ("import config; config.PORT=%d; config.REDIRECT_URI='http://localhost:%d/api/intervals/callback'; "
           "import runpy; runpy.run_path('server.py', run_name='__main__')" % (PORT, PORT))
STATE = {"valid_token": None, "wellness_status": 200}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


opener = urllib.request.build_opener(NoRedirect)


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        if u.path == "/oauth/authorize":
            cats = [s.split(":")[0] for s in q.get("scope", "").split(",")]
            if len(cats) != len(set(cats)):
                return self.send_json(400, {"error": "invalid_request"})
            self.send_response(302)
            self.send_header("Location", f"{q['redirect_uri']}?code=abc&state={urllib.parse.quote(q['state'])}")
            self.end_headers()
            return
        if u.path.startswith("/api/v1/athlete/"):
            auth = self.headers.get("Authorization", "")
            if STATE["wellness_status"] != 200 or auth != "Bearer " + str(STATE["valid_token"]):
                return self.send_json(401, {"error": "bad token"})
            return self.send_json(200, [{"id": "2026-10-27", "weight": 70}])
        self.send_json(404, {})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        f = dict(urllib.parse.parse_qsl(self.rfile.read(n).decode()))
        if self.path == "/api/oauth/token":
            STATE["valid_token"] = "tok-issued"
            # Mirrors the 2026-09-19 response: no expires_in, no refresh_token.
            return self.send_json(200, {"token_type": "bearer", "access_token": "tok-issued",
                                        "scope": f.get("scope", "ACTIVITY:WRITE,WELLNESS:READ"),
                                        "athlete": {"id": "i98765", "name": "T. Rivera"}})
        self.send_json(404, {})


def req(method, url, headers=None):
    r = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with opener.open(r, timeout=20) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def check(label, cond):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        global failures
        failures += 1


failures = 0
threading.Thread(target=HTTPServer(("127.0.0.1", MOCK_PORT), Mock).serve_forever, daemon=True).start()
env = dict(os.environ, INTERVALS_BASE=MOCK)
srv = subprocess.Popen([sys.executable, "-c", WRAPPER], cwd=APP, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(1.5)
try:
    H = {"Authorization": "Bearer tok-rivera"}
    # 1. Connect: JSON with an authorize URL, reachable with the Bearer header.
    s, _, b = req("GET", APP_URL + "/api/intervals/auth/init", H)
    check("auth/init with Bearer returns 200", s == 200)
    url = json.loads(b)["url"]
    check("auth/init without Bearer returns 401", req("GET", APP_URL + "/api/intervals/auth/init")[0] == 401)
    # 2. Authorize step accepts the scope set we now request.
    s, hdr, _ = req("GET", url)
    check("authorize with new scopes is not a 400", s == 302)
    # 3. Callback exchanges the code and connects.
    s, hdr, _ = req("GET", hdr["Location"])
    check("callback redirects to /?connected=1", s == 302 and hdr["Location"] == "/?connected=1")
    s, _, b = req("GET", APP_URL + "/api/intervals/status", H)
    st = json.loads(b)
    check("status is connected for T. Rivera", st.get("connected") is True and st["athlete"]["id"] == "i98765")
    # 4. Wellness works. The token has no expires_in, so it must not be marked expired after an hour.
    check("wellness 200 while connected", req("GET", APP_URL + "/api/intervals/wellness", H)[0] == 200)
    # 5. A 401 from Intervals marks the connection expired, and the status says so.
    STATE["wellness_status"] = 401
    check("wellness passes Intervals 401 through", req("GET", APP_URL + "/api/intervals/wellness", H)[0] == 401)
    s, _, b = req("GET", APP_URL + "/api/intervals/status", H)
    check("status is 'expired, reconnect' after Intervals 401", json.loads(b).get("status") == "expired, reconnect")
    # 6. Reconnecting from the expired state works again.
    STATE["wellness_status"] = 200
    s, _, b = req("GET", APP_URL + "/api/intervals/auth/init", H)
    check("auth/init works after expiry", s == 200)
    # 7. Scope list without duplicate categories is what the server sends.
    check("requested scopes have one entry per category",
          "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE" in urllib.parse.unquote(url))
finally:
    srv.terminate()
    out = srv.communicate(timeout=5)[0]
    print("--- server log ---")
    print(out)
print("FAILURES:", failures)
sys.exit(1 if failures else 0)
