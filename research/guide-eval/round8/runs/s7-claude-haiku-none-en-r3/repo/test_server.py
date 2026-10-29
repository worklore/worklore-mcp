"""Run with: python3 -m unittest test_server -v

Drives the real HTTP handler against a fake Intervals.icu (token endpoint and
wellness API) served from a local thread. No network access needed.
"""
import json, os, threading, unittest, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

FAKE_TOKEN = {"token_type": "bearer", "access_token": "acc-1", "scope": "WELLNESS:READ",
              "athlete": {"id": "i1", "name": "Test Athlete"}}  # no expires_in, no refresh_token


class FakeIntervals(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        if self.path == "/api/oauth/token":
            body = FakeIntervals.token_body
            self.send_response(200 if body else 400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body or {"error": "invalid_request"}).encode())

    def do_GET(self):
        ok = self.headers.get("Authorization") == "Bearer acc-1"
        self.send_response(200 if ok else 401)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}' if ok else b'{"error": "unauthorized"}')


FakeIntervals.token_body = dict(FAKE_TOKEN)
fake = ThreadingHTTPServer(("127.0.0.1", 0), FakeIntervals)
threading.Thread(target=fake.serve_forever, daemon=True).start()
os.environ["INTERVALS_BASE"] = f"http://127.0.0.1:{fake.server_address[1]}"
os.environ["INTERVALS_CLIENT_ID"] = "real-client-id"

import server  # noqa: E402  (must come after the env is set; config reads it at import)

app = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
threading.Thread(target=app.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{app.server_address[1]}"


def call(path, token=None, method="GET"):
    req = urllib.request.Request(BASE + path, method=method)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, _json_or_text(raw), r
    except urllib.error.HTTPError as e:
        with e:
            return e.code, _json_or_text(e.read()), e


def _json_or_text(raw):
    try:
        return json.loads(raw or b"{}")
    except ValueError:
        return raw.decode(errors="replace")


class IntervalsFlow(unittest.TestCase):
    def setUp(self):
        server.CONNECTIONS.clear()
        FakeIntervals.token_body = dict(FAKE_TOKEN)

    def test_auth_init_requires_bearer_and_returns_url(self):
        code, _, _ = call("/api/intervals/auth/init")
        self.assertEqual(code, 401)
        code, body, _ = call("/api/intervals/auth/init", token="tok-okafor")
        self.assertEqual(code, 200)
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(body["url"]).query)
        self.assertEqual(q["client_id"], ["real-client-id"])
        self.assertIn("CALENDAR:WRITE", q["scope"][0])
        self.assertEqual(server.verify_state(q["state"][0]), "u_okafor")

    def test_callback_connects_without_invented_expiry(self):
        state = server.sign_state("u_okafor")
        code, _, r = call(f"/api/intervals/callback?code=abc&state={urllib.parse.quote(state)}")
        self.assertEqual(code, 200)  # urllib follows the redirect to /?connected=1
        c = server.CONNECTIONS["u_okafor"]
        self.assertEqual(c["status"], "connected")
        self.assertIsNone(c["expires_at"])
        code, body, _ = call("/api/intervals/status", token="tok-okafor")
        self.assertTrue(body["connected"])

    def test_upstream_401_marks_connection_for_reconnect(self):
        server.CONNECTIONS["u_okafor"] = {"athlete_id": "i1", "athlete_name": "x",
                                          "access_token": "acc-1", "refresh_token": None,
                                          "scope": None, "expires_at": None, "status": "connected"}
        code, body, _ = call("/api/intervals/wellness", token="tok-okafor")
        self.assertEqual(code, 200)  # token still accepted by fake Intervals
        server.CONNECTIONS["u_okafor"]["access_token"] = "revoked"
        code, body, _ = call("/api/intervals/wellness", token="tok-okafor")
        self.assertEqual(code, 409)
        code, body, _ = call("/api/intervals/status", token="tok-okafor")
        self.assertEqual(body["status"], "expired, reconnect")

    def test_refresh_loop_leaves_unknown_expiry_alone(self):
        server.CONNECTIONS["u_okafor"] = {"athlete_id": "i1", "athlete_name": "x",
                                          "access_token": "acc-1", "refresh_token": None,
                                          "scope": None, "expires_at": None, "status": "connected"}
        class OnePass(Exception):
            pass
        # time.sleep runs once before each pass: let one pass run, then stop the loop.
        with mock.patch.object(server.time, "sleep", side_effect=[None, OnePass()]):
            with self.assertRaises(OnePass):
                server.refresh_tokens()
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "connected")

    def test_callback_bad_state_rejected(self):
        code, body, _ = call("/api/intervals/callback?code=abc&state=bogus")
        self.assertEqual(code, 400)


if __name__ == "__main__":
    unittest.main()
