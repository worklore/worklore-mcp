"""Local OAuth flow checks; Intervals.icu is replaced with in-process fakes."""
import base64
import http.client
import json
import threading
import unittest
import urllib.error
import urllib.parse
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import config
import server


class IntervalsFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join()

    def setUp(self):
        with server.LOCK:
            server.CONNECTIONS.clear()

    def request(self, method, path, user=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port)
        headers = {"Authorization": "Bearer " + user} if user else {}
        conn.request(method, path, headers=headers)
        response = conn.getresponse()
        body = response.read()
        result = response.status, dict(response.getheaders()), json.loads(body) if body else None
        conn.close()
        return result

    def init(self, user="tok-okafor"):
        status, _, body = self.request("POST", "/api/intervals/auth/init", user)
        self.assertEqual(status, 200)
        return urllib.parse.parse_qs(urllib.parse.urlsplit(body["authorize_url"]).query)

    def test_init_requires_auth_and_unique_scopes(self):
        self.assertEqual(self.request("POST", "/api/intervals/auth/init")[0], 401)
        self.assertEqual(self.request("GET", "/api/intervals/auth/init", "tok-okafor")[0], 404)
        query = self.init()
        self.assertEqual(query["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(query["redirect_uri"], [config.REDIRECT_URI])
        self.assertEqual(server.verify_state(query["state"][0]), "u_okafor")

    def test_callback_connection_and_revocation(self):
        state = self.init()["state"][0]
        token = {"access_token": "local-test-token", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "Athlete"}}
        with patch.object(server, "post_form", return_value=token) as exchange:
            path = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "abc", "state": state})
            status, headers, _ = self.request("GET", path)
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        self.assertEqual(exchange.call_args.args[1], {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "abc"})
        self.assertEqual(self.request("GET", "/api/intervals/status", "tok-okafor")[2]["connected"], True)
        with patch.object(server, "intervals_get", return_value=(200, [{"date": "2026-10-27"}])):
            self.assertEqual(self.request("GET", "/api/intervals/wellness", "tok-okafor")[2],
                             [{"date": "2026-10-27"}])
        revoked = urllib.error.HTTPError("local", 401, "Unauthorized", {}, None)
        with patch.object(server, "intervals_get", side_effect=revoked):
            self.assertEqual(self.request("GET", "/api/intervals/wellness", "tok-okafor")[0], 401)
        with server.LOCK:
            self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])
        self.assertEqual(self.request("GET", "/api/intervals/status", "tok-okafor")[2],
                         {"connected": False, "status": "reconnect required"})

    def test_bad_state_and_account_mismatch(self):
        self.assertEqual(self.request("GET", "/api/intervals/callback?code=abc&state=%%%" )[0], 400)
        state = self.init()["state"][0]
        with server.LOCK:
            server.CONNECTIONS["u_okafor"] = {"athlete_id": "original", "athlete_name": "Original",
                "access_token": "old", "scope": config.SCOPES, "status": "connected"}
        with patch.object(server, "post_form", return_value={"access_token": "new",
                "athlete": {"id": "someone-else", "name": "Other"}}):
            path = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "abc", "state": state})
            self.assertEqual(self.request("GET", path)[0], 409)
        with server.LOCK:
            self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "old")
        raw = base64.urlsafe_b64decode(state).decode().replace("intervals_oauth", "other_purpose")
        bad_purpose = base64.urlsafe_b64encode(raw.encode()).decode()
        self.assertIsNone(server.verify_state(bad_purpose))


if __name__ == "__main__":
    unittest.main()
