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
        with server.LOCK:
            server.CONNECTIONS.clear()

    def request(self, path, method="GET", token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, data=b"" if method == "POST" else None,
                                     headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                if response.headers.get_content_type() == "application/json":
                    return response.status, json.loads(response.read())
                return response.status, response.url
        except urllib.error.HTTPError as error:
            with error:
                return error.code, json.loads(error.read())

    def test_init_is_authenticated_post_and_has_unique_scopes(self):
        self.assertEqual(self.request("/api/intervals/auth/init")[0], 405)
        self.assertEqual(self.request("/api/intervals/auth/init", "POST")[0], 401)
        status, body = self.request("/api/intervals/auth/init", "POST", "tok-okafor")
        self.assertEqual(status, 200)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(body["authorize_url"]).query)
        self.assertEqual(query["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(server.verify_state(query["state"][0]), "u_okafor")

    def test_exchange_connection_and_revocation(self):
        token_response = {"access_token": "intervals-token", "scope": config.SCOPES,
                          "athlete": {"id": "i123", "name": "C. Okafor"}}
        with patch.object(server, "post_form", return_value=token_response) as exchange:
            callback = "/api/intervals/callback?" + urllib.parse.urlencode(
                {"code": "auth-code", "state": server.sign_state("u_okafor")})
            self.assertEqual(self.request(callback)[0], 200)
        self.assertEqual(exchange.call_args.args[1], {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "auth-code"})
        status, body = self.request("/api/intervals/status", token="tok-okafor")
        self.assertEqual((status, body["connected"]), (200, True))
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])
        with patch.object(server, "intervals_get", side_effect=urllib.error.HTTPError(
                "https://intervals.icu/test", 401, "Unauthorized", {}, None)):
            self.assertEqual(self.request("/api/intervals/wellness", token="tok-okafor")[0], 401)
        status, body = self.request("/api/intervals/status", token="tok-okafor")
        self.assertEqual((status, body["connected"], body["status"]),
                         (200, False, "reconnect required"))
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])

    def test_reconnect_rejects_different_athlete(self):
        server.store_connection("u_okafor", {"access_token": "old", "athlete": {"id": "i123"}})
        with patch.object(server, "post_form", return_value={"access_token": "new", "athlete": {"id": "i456"}}):
            callback = "/api/intervals/callback?" + urllib.parse.urlencode(
                {"code": "auth-code", "state": server.sign_state("u_okafor")})
            self.assertEqual(self.request(callback)[0], 409)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "old")

    def test_state_rejects_tampering_and_expiry(self):
        state = server.sign_state("u_okafor")
        self.assertIsNone(server.verify_state(state[:-3] + "abc"))
        with patch.object(server.time, "time", return_value=server.time.time() + 901):
            self.assertIsNone(server.verify_state(state))


if __name__ == "__main__":
    unittest.main()
