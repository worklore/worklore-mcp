"""Local HTTP checks for the Intervals.icu connection flow."""
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


class ConnectionFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join()

    def setUp(self):
        server.CONNECTIONS.clear()

    def request(self, path, method="GET", token="tok-okafor"):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, data=b"" if method == "POST" else None,
                                     headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, response.headers, response.read()
        except urllib.error.HTTPError as error:
            with error:
                return error.code, error.headers, error.read()

    def test_authenticated_init_and_provider_callback(self):
        self.assertEqual(self.request("/api/intervals/auth/init")[0], 404)
        self.assertEqual(self.request("/api/intervals/auth/init", "POST", token=None)[0], 401)
        code, _, body = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(code, 200)
        url = json.loads(body)["authorize_url"]
        parsed = urllib.parse.urlsplit(url)
        params = dict(urllib.parse.parse_qsl(parsed.query))
        self.assertEqual(parsed.path, "/oauth/authorize")
        self.assertEqual(params["scope"], "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE")
        self.assertEqual(server.verify_state(params["state"]), "u_okafor")

        token_reply = {"access_token": "perpetual-token", "scope": params["scope"],
                       "athlete": {"id": "i123", "name": "C. Okafor"}}
        with patch.object(server, "post_form", return_value=token_reply) as exchange:
            callback = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "abc", "state": params["state"]})
            code, headers, _ = self.request(callback, token=None)
            self.assertEqual(code, 200)  # urllib follows the callback redirect to the SPA
            self.assertEqual(headers.get_content_type(), "text/html")
            exchange.assert_called_once_with(server.TOKEN_URL, {
                "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "abc"})
        with patch.object(server.time, "time", return_value=server.time.time() + 7200):
            code, _, body = self.request("/api/intervals/status")
        self.assertEqual(code, 200)
        self.assertTrue(json.loads(body)["connected"])

    def test_revocation_prompts_reconnect(self):
        server.store_connection("u_okafor", {"access_token": "revoked", "athlete": {"id": "i123"}})
        error = urllib.error.HTTPError("local", 401, "Unauthorized", {}, io.BytesIO(b""))
        with patch.object(server, "intervals_get", side_effect=error):
            self.assertEqual(self.request("/api/intervals/wellness")[0], 401)
        code, _, body = self.request("/api/intervals/status")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body), {"connected": False, "status": "reconnect"})

    def test_reconnect_cannot_change_athlete(self):
        server.store_connection("u_okafor", {"access_token": "old", "athlete": {"id": "i123"}})
        with self.assertRaisesRegex(ValueError, "differs"):
            server.store_connection("u_okafor", {"access_token": "new", "athlete": {"id": "i999"}})
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "old")

    def test_state_rejects_tampering_and_expiry(self):
        state = server.sign_state("u_okafor")
        self.assertIsNone(server.verify_state(state[:-4] + "abcd"))
        with patch.object(server.time, "time", return_value=server.time.time() + 901):
            self.assertIsNone(server.verify_state(state))


if __name__ == "__main__":
    unittest.main()
