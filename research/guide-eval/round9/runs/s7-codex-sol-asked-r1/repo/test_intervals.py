"""Local OAuth flow checks; no requests are sent to Intervals.icu."""
import http.client
import io
import json
import threading
import unittest
import urllib.error
import urllib.parse
from unittest.mock import patch

import config
import server


class IntervalsFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join()

    def setUp(self):
        server.CONNECTIONS.clear()

    def request(self, method, path, token=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port)
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        conn.request(method, path, headers=headers)
        res = conn.getresponse()
        body = res.read()
        result = res.status, dict(res.getheaders()), json.loads(body) if body else None
        conn.close()
        return result

    def init(self):
        status, _, data = self.request("POST", "/api/intervals/auth/init", "tok-okafor")
        self.assertEqual(status, 200)
        url = urllib.parse.urlsplit(data["authorize_url"])
        return urllib.parse.parse_qs(url.query)

    def test_authenticated_init_and_valid_scope(self):
        self.assertEqual(self.request("POST", "/api/intervals/auth/init")[0], 401)
        self.assertEqual(self.request("GET", "/api/intervals/auth/init", "tok-okafor")[0], 404)
        query = self.init()
        self.assertEqual(query["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(server.verify_state(query["state"][0]), "u_okafor")

    def test_exchange_accepts_provider_response_without_expiry(self):
        query = self.init()
        token = {"access_token": "provider-token", "athlete": {"id": "i123", "name": "C. Okafor"},
                 "scope": config.SCOPES}
        with patch.object(server, "post_form", return_value=token) as exchange:
            path = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "sample-code", "state": query["state"][0]})
            status, headers, _ = self.request("GET", path)
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        exchange.assert_called_once_with(server.TOKEN_URL, {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "sample-code"})
        self.assertEqual(self.request("GET", "/api/intervals/status", "tok-okafor")[2]["connected"], True)
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])
        self.assertNotIn("refresh_token", server.CONNECTIONS["u_okafor"])

    def test_revocation_on_provider_401_only(self):
        server.store_connection("u_okafor", {"access_token": "provider-token", "athlete": {"id": "i123"}})
        with patch.object(server, "intervals_get", side_effect=urllib.error.HTTPError("x", 503, "down", {}, io.BytesIO())):
            self.assertEqual(self.request("GET", "/api/intervals/wellness", "tok-okafor")[0], 503)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "connected")
        with patch.object(server, "intervals_get", side_effect=urllib.error.HTTPError("x", 401, "revoked", {}, io.BytesIO())):
            self.assertEqual(self.request("GET", "/api/intervals/wellness", "tok-okafor")[0], 409)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "expired, reconnect")
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])

    def test_callback_rejects_invalid_state_and_different_athlete(self):
        query = self.init()
        state = query["state"][0]
        self.assertIsNone(server.verify_state(state + "x"))
        self.assertEqual(self.request("GET", "/api/intervals/callback?code=x&state=invalid")[0], 400)
        server.store_connection("u_okafor", {"access_token": "old", "athlete": {"id": "i123"}})
        with patch.object(server, "exchange_code", return_value={"access_token": "new", "athlete": {"id": "i456"}}):
            path = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "x", "state": state})
            self.assertEqual(self.request("GET", path)[0], 409)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "old")


if __name__ == "__main__":
    unittest.main()
