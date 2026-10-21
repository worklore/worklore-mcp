"""Local OAuth flow checks; no requests to Intervals.icu."""
import io
import json
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import config
import server


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class IntervalsFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.http.server_port}"
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()

    def setUp(self):
        server.CONNECTIONS.clear()

    def request(self, path, method="GET", authenticated=True):
        headers = {"Authorization": "Bearer tok-okafor"} if authenticated else {}
        req = urllib.request.Request(self.base + path, headers=headers, method=method)
        try:
            response = urllib.request.build_opener(NoRedirect).open(req)
        except urllib.error.HTTPError as e:
            response = e
        with response:
            body = response.read()
            return response.status, json.loads(body) if body else {}, response.headers

    def test_init_needs_auth_and_returns_unique_scopes(self):
        self.assertEqual(self.request("/api/intervals/auth/init", "POST", False)[0], 401)
        self.assertEqual(self.request("/api/intervals/auth/init")[0], 404)
        status, data, _ = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(status, 200)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(data["authorize_url"]).query)
        self.assertEqual(query["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(server.verify_state(query["state"][0]), "u_okafor")

    def test_callback_token_exchange_and_revocation(self):
        init = self.request("/api/intervals/auth/init", "POST")[1]
        state = urllib.parse.parse_qs(urllib.parse.urlsplit(init["authorize_url"]).query)["state"][0]
        callback = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "test-code", "state": state})
        token = {"access_token": "test-token", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "C. Okafor"}}
        with patch.object(server, "post_form", return_value=token) as post:
            status, _, headers = self.request(callback, authenticated=False)
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        self.assertEqual(post.call_args.args[1], {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "test-code"
        })
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "connected")
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])
        self.assertTrue(self.request("/api/intervals/status")[1]["connected"])

        revoked = urllib.error.HTTPError("local-mock", 401, "Unauthorized", {}, io.BytesIO())
        with patch.object(server, "intervals_get", side_effect=revoked):
            self.assertEqual(self.request("/api/intervals/wellness")[0], 401)
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])
        self.assertEqual(self.request("/api/intervals/status")[1]["status"], "revoked, reconnect")

    def test_reconnect_cannot_switch_athlete(self):
        server.store_connection("u_okafor", {"access_token": "old", "athlete": {"id": "i123"}})
        with self.assertRaisesRegex(ValueError, "differs"):
            server.store_connection("u_okafor", {"access_token": "new", "athlete": {"id": "i456"}})
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "old")


if __name__ == "__main__":
    unittest.main()
