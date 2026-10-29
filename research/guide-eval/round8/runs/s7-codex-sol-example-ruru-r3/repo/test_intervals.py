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
        with server.LOCK:
            server.CONNECTIONS.clear()

    def request(self, path, method="GET", auth=True):
        headers = {"Authorization": "Bearer tok-okafor"} if auth else {}
        req = urllib.request.Request(self.base + path, data=b"" if method == "POST" else None,
                                     headers=headers, method=method)
        try:
            response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_connection_and_revocation(self):
        self.assertEqual(404, self.request("/api/intervals/auth/init")[0])
        self.assertEqual(401, self.request("/api/intervals/auth/init", "POST", auth=False)[0])
        code, body = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(200, code)
        url = urllib.parse.urlsplit(body["authorize_url"])
        params = urllib.parse.parse_qs(url.query)
        self.assertEqual(config.SCOPES, params["scope"][0])
        self.assertEqual(len(config.SCOPES.split(",")), len({s.split(":")[0] for s in config.SCOPES.split(",")}))
        state = params["state"][0]
        self.assertEqual("u_okafor", server.verify_state(state))

        token = {"access_token": "secret", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "C. Okafor"}}
        with patch.object(server, "exchange_code", return_value=token) as exchange:
            req = urllib.request.Request(self.base + "/api/intervals/callback?" +
                                         urllib.parse.urlencode({"code": "sample", "state": state}))
            with urllib.request.urlopen(req) as response:
                self.assertEqual(200, response.status)
            exchange.assert_called_once_with("sample")
        self.assertEqual("connected", server.CONNECTIONS["u_okafor"]["status"])
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])
        self.assertNotIn("refresh_token", server.CONNECTIONS["u_okafor"])

        with patch.object(server, "intervals_get", return_value=(200, {"ok": True})):
            self.assertEqual((200, {"ok": True}), self.request("/api/intervals/wellness"))
        revoked = urllib.error.HTTPError("mock", 401, "Unauthorized", {}, io.BytesIO())
        with patch.object(server, "intervals_get", side_effect=revoked):
            self.assertEqual(409, self.request("/api/intervals/wellness")[0])
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])
        self.assertEqual("reconnect required", self.request("/api/intervals/status")[1]["status"])

    def test_token_exchange_fields_and_account_mismatch(self):
        with patch.object(server, "post_form", return_value={}) as post:
            server.exchange_code("sample")
        self.assertEqual({"client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET,
                          "code": "sample"}, post.call_args.args[1])
        token = {"access_token": "one", "athlete": {"id": "i123"}}
        self.assertTrue(server.store_connection("u_okafor", token))
        self.assertFalse(server.store_connection("u_okafor", {
            "access_token": "two", "athlete": {"id": "i999"}}))
        self.assertEqual("one", server.CONNECTIONS["u_okafor"]["access_token"])

    def test_state_rejects_tampering_and_expiry(self):
        state = server.sign_state("u_okafor")
        self.assertIsNone(server.verify_state(state + "x"))
        with patch.object(server.time, "time", return_value=server.time.time() + 901):
            self.assertIsNone(server.verify_state(state))


if __name__ == "__main__":
    unittest.main()
