"""Connection flow checks, run against a local fake of Intervals.icu (no network).

The fake follows what logs/connect-attempt.log shows: token responses carry no
expires_in and no refresh_token, a duplicated scope area is rejected on the
authorize step, and the token exchange takes client_id, client_secret and code.

Run from this directory: python3 -m unittest -v test_connect
"""
import hashlib, hmac, http.client, json, os, threading, time, unittest
import urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FAKE = {"revoked": set(), "token_forms": []}
ATHLETE = {"id": "i98765", "name": "T. Rivera"}
OTHER_ATHLETE = {"id": "i55555", "name": "someone else"}


class FakeIntervals(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        q = dict(urllib.parse.parse_qsl(url.query))
        if url.path == "/oauth/authorize":
            areas = [s.split(":")[0] for s in q.get("scope", "").split(",")]
            if len(areas) != len(set(areas)):
                return self.reply(400, {"error": "Duplicate scope"})
            return self.reply(200, {"consent": "screen"})
        if url.path.startswith("/api/v1/athlete/"):
            token = (self.headers.get("Authorization") or "")[len("Bearer "):]
            if not token or token in FAKE["revoked"]:
                return self.reply(401, {"error": "unauthorized"})
            return self.reply(200, [{"id": "2026-10-20", "ctl": 42.0}])
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        form = dict(urllib.parse.parse_qsl(self.rfile.read(length).decode()))
        if self.path == "/api/oauth/token":
            FAKE["token_forms"].append(form)
            if set(form) != {"client_id", "client_secret", "code"}:
                return self.reply(400, {"error": "invalid_request"})
            athlete = OTHER_ATHLETE if form["code"] == "other-code" else ATHLETE
            return self.reply(200, {"token_type": "bearer", "access_token": "tok-" + form["code"],
                                    "scope": "ACTIVITY:WRITE,WELLNESS:READ", "athlete": athlete})
        self.reply(404, {"error": "not found"})


FAKE_SERVER = ThreadingHTTPServer(("127.0.0.1", 0), FakeIntervals)
threading.Thread(target=FAKE_SERVER.serve_forever, daemon=True).start()
os.environ["INTERVALS_BASE"] = f"http://127.0.0.1:{FAKE_SERVER.server_address[1]}"

import config  # noqa: E402  (reads INTERVALS_BASE, so import after setting it)
import server  # noqa: E402

server.Handler.log_message = lambda self, *args: None
APP = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
threading.Thread(target=APP.serve_forever, daemon=True).start()
APP_PORT = APP.server_address[1]


def call(method, path, token=None):
    conn = http.client.HTTPConnection("127.0.0.1", APP_PORT)
    headers = {"Authorization": "Bearer " + token} if token else {}
    conn.request(method, path, headers=headers)
    r = conn.getresponse()
    data = r.read()
    location = r.getheader("Location")
    conn.close()
    body = json.loads(data) if r.getheader("Content-Type", "").startswith("application/json") else None
    return r.status, body, location


def fetch_status(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def forge_state(claims):
    """A state signed with the app's real secret but with claims of our choosing."""
    header = server.b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = server.b64url(json.dumps(claims).encode())
    sig = server.b64url(hmac.new(config.APP_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


class ConnectionFlow(unittest.TestCase):
    def setUp(self):
        server.CONNECTIONS.clear()
        FAKE["revoked"].clear()
        FAKE["token_forms"].clear()

    def init_state(self, token="tok-rivera"):
        status, body, _ = call("POST", "/api/intervals/auth/init", token)
        self.assertEqual(status, 200)
        return urllib.parse.parse_qs(urllib.parse.urlsplit(body["authorize_url"]).query)["state"][0]

    def callback(self, state, code="good-code"):
        return call("GET", f"/api/intervals/callback?code={code}&state={urllib.parse.quote(state)}")

    def connect(self, token="tok-rivera", code="good-code"):
        return self.callback(self.init_state(token), code)

    def test_init_is_post_only(self):
        status, _, location = call("GET", "/api/intervals/auth/init", "tok-rivera")
        self.assertEqual(status, 404)
        self.assertIsNone(location)

    def test_init_needs_auth(self):
        status, _, _ = call("POST", "/api/intervals/auth/init")
        self.assertEqual(status, 401)

    def test_authorize_url_is_accepted_by_intervals(self):
        status, body, _ = call("POST", "/api/intervals/auth/init", "tok-rivera")
        self.assertEqual(status, 200)
        self.assertEqual(fetch_status(body["authorize_url"]), 200)

    def test_scope_lists_each_area_once(self):
        areas = [s.split(":")[0] for s in config.SCOPES.split(",")]
        self.assertEqual(len(areas), len(set(areas)), config.SCOPES)

    def test_full_flow_has_no_expiry_and_reads_wellness(self):
        status, _, location = self.connect()
        self.assertEqual((status, location), (302, "/?connected=1"))
        self.assertEqual(set(FAKE["token_forms"][-1]), {"client_id", "client_secret", "code"})
        conn = server.CONNECTIONS["u_rivera"]
        self.assertEqual(conn["athlete_id"], "i98765")
        self.assertNotIn("expires_at", conn)
        status, _, _ = call("GET", "/api/intervals/status", "tok-rivera")
        self.assertEqual(status, 200)
        status, body, _ = call("GET", "/api/intervals/wellness", "tok-rivera")
        self.assertEqual(status, 200)
        self.assertEqual(body, [{"id": "2026-10-20", "ctl": 42.0}])

    def test_revoked_token_asks_for_reconnect_and_reconnect_works(self):
        self.connect()
        FAKE["revoked"].add("tok-good-code")
        status, body, _ = call("GET", "/api/intervals/wellness", "tok-rivera")
        self.assertEqual((status, body["status"]), (409, "reconnect"))
        status, body, _ = call("GET", "/api/intervals/status", "tok-rivera")
        self.assertEqual((body["connected"], body["status"]), (False, "reconnect"))
        self.assertIsNone(server.CONNECTIONS["u_rivera"]["access_token"])

        FAKE["revoked"].clear()
        status, _, location = self.connect(code="second-code")
        self.assertEqual((status, location), (302, "/?connected=1"))
        status, _, _ = call("GET", "/api/intervals/wellness", "tok-rivera")
        self.assertEqual(status, 200)

    def test_reconnect_as_a_different_athlete_is_refused(self):
        self.connect()
        FAKE["revoked"].add("tok-good-code")
        call("GET", "/api/intervals/wellness", "tok-rivera")
        status, _, _ = self.connect(code="other-code")
        self.assertEqual(status, 409)
        self.assertEqual(server.CONNECTIONS["u_rivera"]["athlete_id"], "i98765")
        self.assertEqual(server.CONNECTIONS["u_rivera"]["status"], "reconnect")

    def test_bad_states_are_rejected(self):
        now = int(time.time())
        valid = self.init_state()
        parts = valid.split(".")
        tampered_body = server.b64url(json.dumps(
            {"sub": "u_okafor", "purpose": "intervals_oauth", "iat": now, "exp": now + 900}).encode())
        cases = {
            "tampered": f"{parts[0]}.{tampered_body}.{parts[2]}",
            "expired": forge_state({"sub": "u_rivera", "purpose": "intervals_oauth", "exp": now - 1}),
            "wrong purpose": forge_state({"sub": "u_rivera", "purpose": "login", "exp": now + 900}),
            "no state": None,
        }
        for name, state in cases.items():
            with self.subTest(name):
                status, _, _ = self.callback(state) if state else call("GET", "/api/intervals/callback?code=x")
                self.assertEqual(status, 400)
                self.assertNotIn("u_rivera", server.CONNECTIONS)
                self.assertNotIn("u_okafor", server.CONNECTIONS)


if __name__ == "__main__":
    unittest.main()
