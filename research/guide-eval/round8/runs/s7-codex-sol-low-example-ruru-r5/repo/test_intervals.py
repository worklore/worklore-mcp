import json
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import config
import server


class IntervalsFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.http.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()

    def setUp(self):
        server.CONNECTIONS.clear()

    def request(self, path, method="GET", auth=True):
        headers = {"Authorization": "Bearer tok-okafor"} if auth else {}
        req = urllib.request.Request(self.base + path, headers=headers, method=method)
        try:
            return urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            return e

    def test_authenticated_post_and_scope(self):
        self.assertEqual(self.request("/api/intervals/auth/init").status, 404)
        self.assertEqual(self.request("/api/intervals/auth/init", "POST", False).status, 401)
        res = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(res.status, 200)
        url = json.load(res)["authorize_url"]
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

    def test_callback_connection_and_revocation(self):
        token = {"access_token": "secret", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "Athlete"}}
        with patch.object(server, "exchange_code", return_value=token) as exchange, \
             patch.object(server.Handler, "redirect", lambda handler, url: handler.send_json(200, {"redirect": url})):
            res = self.request("/api/intervals/callback?" + urllib.parse.urlencode({
                "state": server.sign_state("u_okafor"), "code": "abc"}), auth=False)
            self.assertEqual(json.load(res)["redirect"], "/?connected=1")
            exchange.assert_called_once_with("abc")
        self.assertTrue(json.load(self.request("/api/intervals/status"))["connected"])
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])
        with patch.object(server, "intervals_get", side_effect=urllib.error.HTTPError("test", 401, "Unauthorized", {}, None)):
            self.assertEqual(self.request("/api/intervals/wellness").status, 401)
        self.assertFalse(json.load(self.request("/api/intervals/status"))["connected"])
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])

    def test_account_mismatch_keeps_existing_connection(self):
        server.store_connection("u_okafor", {"access_token": "first", "athlete": {"id": "i1"}})
        with self.assertRaisesRegex(ValueError, "different Intervals athlete"):
            server.store_connection("u_okafor", {"access_token": "second", "athlete": {"id": "i2"}})
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "first")

    def test_exchange_fields_and_state_validation(self):
        with patch.object(server, "post_form", return_value={}) as post:
            server.exchange_code("abc")
        post.assert_called_once_with(server.TOKEN_URL, {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "abc"})
        with patch.object(server.time, "time", return_value=1000):
            state = server.sign_state("u_okafor")
        with patch.object(server.time, "time", return_value=1901):
            self.assertIsNone(server.verify_state(state))
        self.assertIsNone(server.verify_state(state + "x"))


if __name__ == "__main__":
    unittest.main()
