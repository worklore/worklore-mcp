"""Local OAuth regression tests; no requests to Intervals.icu."""
import io
import json
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from unittest.mock import patch

import config
import server


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class IntervalsFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
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
        req = urllib.request.Request(self.base + path, method=method, headers=headers)
        opener = urllib.request.build_opener(NoRedirect)
        try:
            with opener.open(req) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as error:
            try:
                return error.code, dict(error.headers), error.read()
            finally:
                error.close()

    def test_connect_and_revocation(self):
        status, _, _ = self.request("/api/intervals/auth/init", method="POST", auth=False)
        self.assertEqual(status, 401)
        status, _, body = self.request("/api/intervals/auth/init", method="POST")
        self.assertEqual(status, 200)
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(json.loads(body)["authorize_url"]).query)
        self.assertEqual(params["scope"], [config.SCOPES])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")
        callback = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "sample", "state": params["state"][0]})
        token = {"access_token": "local-token", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "C. Okafor"}}
        with patch.object(server, "exchange_code", return_value=token) as exchange:
            status, headers, _ = self.request(callback, auth=False)
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        exchange.assert_called_once_with("sample")
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])
        self.assertNotIn("refresh_token", server.CONNECTIONS["u_okafor"])
        with patch.object(server, "intervals_get", return_value=(200, {"wellness": []})):
            status, _, _ = self.request("/api/intervals/wellness")
        self.assertEqual(status, 200)
        revoked = urllib.error.HTTPError("local", 401, "Unauthorized", {}, io.BytesIO())
        with patch.object(server, "intervals_get", side_effect=revoked):
            status, _, body = self.request("/api/intervals/wellness")
        self.assertEqual(status, 409)
        self.assertIn(b"reconnect", body)
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])
        status, _, body = self.request("/api/intervals/status")
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(body)["connected"])

    def test_rejects_bad_state_and_other_athlete(self):
        status, _, _ = self.request("/api/intervals/callback?code=x&state=garbage", auth=False)
        self.assertEqual(status, 400)
        server.store_connection("u_okafor", {"access_token": "old", "athlete": {"id": "i123"}})
        state = server.sign_state("u_okafor")
        callback = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "sample", "state": state})
        with patch.object(server, "exchange_code", return_value={"access_token": "new", "athlete": {"id": "i999"}}):
            status, _, _ = self.request(callback, auth=False)
        self.assertEqual(status, 409)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "old")

    def test_token_exchange_fields(self):
        with patch.object(server, "post_form", return_value={}) as post:
            server.exchange_code("sample")
        self.assertEqual(post.call_args.args[1], {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "sample"})


if __name__ == "__main__":
    unittest.main()
