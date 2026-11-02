import http.client
import json
import threading
import unittest
import urllib.parse
from unittest.mock import patch
from http.server import ThreadingHTTPServer

import config
import server


class IntervalsConnectionTests(unittest.TestCase):
    def setUp(self):
        server.CONNECTIONS.clear()
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()
        server.CONNECTIONS.clear()

    def get(self, path, token=None, accept=None):
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + token
        if accept:
            headers["Accept"] = accept
        conn = http.client.HTTPConnection("127.0.0.1", self.http.server_port)
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        status = response.status
        location = response.getheader("Location")
        body = response.read()
        conn.close()
        return status, location, body

    def test_authenticated_init_returns_authorize_url_with_required_scopes(self):
        status, _, body = self.get("/api/intervals/auth/init", "tok-okafor", "application/json")
        self.assertEqual(status, 200)
        url = json.loads(body)["authorize_url"]
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        self.assertEqual(query["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(server.verify_state(query["state"][0]), "u_okafor")
        self.assertEqual(self.get("/api/intervals/auth/init", accept="application/json")[0], 401)

    def test_code_exchange_uses_intervals_token_fields(self):
        with patch.object(server, "post_form", return_value={"access_token": "test"}) as post:
            server.exchange_code("test-code")
        post.assert_called_once_with(server.TOKEN_URL, {
            "client_id": config.CLIENT_ID,
            "client_secret": config.CLIENT_SECRET,
            "code": "test-code",
        })

    def test_callback_keeps_provider_token_without_expiry_connected(self):
        _, _, body = self.get("/api/intervals/auth/init", "tok-rivera", "application/json")
        state = urllib.parse.parse_qs(urllib.parse.urlsplit(json.loads(body)["authorize_url"]).query)["state"][0]
        token_response = {
            "access_token": "test-access-token",
            "scope": config.SCOPES,
            "athlete": {"id": "i98765", "name": "T. Rivera"},
        }
        with patch.object(server, "exchange_code", return_value=token_response) as exchange:
            status, location, _ = self.get("/api/intervals/callback?" + urllib.parse.urlencode({"code": "test-code", "state": state}))
        self.assertEqual((status, location), (302, "/?connected=1"))
        exchange.assert_called_once_with("test-code")
        self.assertIsNone(server.CONNECTIONS["u_rivera"]["expires_at"])
        with patch.object(server.time, "time", return_value=server.time.time() + 7200):
            status, _, body = self.get("/api/intervals/status", "tok-rivera")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["connected"])


if __name__ == "__main__":
    unittest.main()
