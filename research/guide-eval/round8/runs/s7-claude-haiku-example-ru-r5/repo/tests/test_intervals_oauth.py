"""End-to-end check of the Intervals.icu connection against a fake Intervals.

Run from the repo root: python3 -m unittest tests.test_intervals_oauth -v
"""
import json, os, sys, threading, unittest, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FAKE_PORT = 18766
os.environ["INTERVALS_BASE"] = f"http://127.0.0.1:{FAKE_PORT}"

import config  # noqa: E402
import server  # noqa: E402

# --- fake Intervals.icu -------------------------------------------------------
VALID_TOKENS = set()
ISSUED_CODE = "code-1"


def areas(scope):
    return [s.split(":")[0] for s in scope.split(",")]


class FakeIntervals(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, code, obj, headers=None):
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
            scope = q.get("scope", "")
            if len(areas(scope)) != len(set(areas(scope))):
                return self.send_json(400, {"error": "invalid_request"})
            if q.get("client_id") != config.CLIENT_ID:
                return self.send_json(400, {"error": "invalid_request"})
            self.send_response(302)
            self.send_header("Location", q["redirect_uri"] + "?" + urllib.parse.urlencode(
                {"code": ISSUED_CODE, "state": q["state"]}))
            self.end_headers()
            return
        if url.path == "/api/v1/athlete/i1/wellness":
            auth = self.headers.get("Authorization", "")
            if auth[7:] not in VALID_TOKENS:
                return self.send_json(401, {"error": "unauthorized"})
            return self.send_json(200, [{"id": "2026-10-27", "restingHR": 48}])
        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        form = dict(urllib.parse.parse_qsl(self.rfile.read(length).decode()))
        if self.path != "/api/oauth/token" or form.get("code") != ISSUED_CODE:
            return self.send_json(400, {"error": "invalid_request"})
        VALID_TOKENS.add("tok-i1")
        # Like the real provider: no refresh_token, no expires_in.
        self.send_json(200, {"token_type": "bearer", "access_token": "tok-i1",
                             "scope": form.get("scope", config.SCOPES),
                             "athlete": {"id": "i1", "name": "T. Rivera"}})


# --- helpers -----------------------------------------------------------------
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def call(url, method="GET", token=None):
    headers = {"Authorization": "Bearer " + token} if token else {}
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with OPENER.open(req, timeout=10) as r:
            return r.status, r.headers, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, e.headers, json.loads(e.read() or b"{}")


class IntervalsOAuthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake = ThreadingHTTPServer(("127.0.0.1", FAKE_PORT), FakeIntervals)
        threading.Thread(target=cls.fake.serve_forever, daemon=True).start()
        cls.app = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.app.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.app.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.fake.shutdown()
        cls.fake.server_close()
        cls.app.shutdown()
        cls.app.server_close()

    def setUp(self):
        server.CONNECTIONS.clear()
        VALID_TOKENS.clear()

    def test_connect_button_endpoint_is_post_and_returns_url(self):
        status, _, _ = call(self.base + "/api/intervals/auth/init", "GET", "tok-rivera")
        self.assertEqual(status, 404, "GET navigation must not be the init endpoint")
        status, _, body = call(self.base + "/api/intervals/auth/init", "POST", "tok-rivera")
        self.assertEqual(status, 200)
        self.assertTrue(body["authorize_url"].startswith(config.INTERVALS_BASE + "/oauth/authorize?"))

    def test_init_without_auth_header_is_rejected(self):
        status, _, _ = call(self.base + "/api/intervals/auth/init", "POST")
        self.assertEqual(status, 401)

    def connect_as_rivera(self):
        _, _, init = call(self.base + "/api/intervals/auth/init", "POST", "tok-rivera")
        # Browser goes to Intervals; Intervals redirects back to our callback.
        _, headers, _ = call(init["authorize_url"])
        return self.to_app(headers["Location"])

    def to_app(self, location):
        # Intervals redirects to REDIRECT_URI (fixed port); point it at the test server.
        parts = urllib.parse.urlsplit(location)
        return self.base + parts.path + "?" + parts.query

    def test_full_flow_connects_and_reads_wellness(self):
        status, headers, _ = call(self.connect_as_rivera())  # callback carries no auth header
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/?connected=1")

        status, _, st = call(self.base + "/api/intervals/status", "GET", "tok-rivera")
        self.assertTrue(st["connected"])
        self.assertEqual(st["athlete"]["id"], "i1")

        status, _, data = call(self.base + "/api/intervals/wellness", "GET", "tok-rivera")
        self.assertEqual(status, 200)
        self.assertEqual(data[0]["restingHR"], 48)

    def test_connection_does_not_expire_by_itself(self):
        call(self.connect_as_rivera())
        conn = server.CONNECTIONS["u_rivera"]
        self.assertNotIn("expires_at", conn)
        self.assertEqual(conn["status"], "connected")

    def test_revoked_token_degrades_to_reconnect(self):
        call(self.connect_as_rivera())
        VALID_TOKENS.clear()  # athlete revoked the app in Intervals

        status, _, _ = call(self.base + "/api/intervals/wellness", "GET", "tok-rivera")
        self.assertEqual(status, 409)
        _, _, st = call(self.base + "/api/intervals/status", "GET", "tok-rivera")
        self.assertFalse(st["connected"])
        self.assertEqual(st["status"], "revoked, reconnect")

    def test_old_scope_with_duplicate_area_is_rejected(self):
        old = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"
        url = config.INTERVALS_BASE + "/oauth/authorize?" + urllib.parse.urlencode(
            {"client_id": config.CLIENT_ID, "redirect_uri": config.REDIRECT_URI, "scope": old},
            safe=":,")
        status, _, _ = call(url)
        self.assertEqual(status, 400)

    def test_configured_scopes_have_one_entry_per_area(self):
        self.assertEqual(len(areas(config.SCOPES)), len(set(areas(config.SCOPES))))


if __name__ == "__main__":
    unittest.main()
