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
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class IntervalsFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.opener = urllib.request.build_opener(NoRedirect)
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
        with server.LOCK:
            server.CONNECTIONS.clear()

    def request(self, path, method="GET", token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, data=b"" if method == "POST" else None,
                                     headers=headers, method=method)
        try:
            response = self.opener.open(req)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read()
            return response.status, response.headers, json.loads(body) if body else None

    def test_init_requires_authenticated_post_and_unique_scopes(self):
        self.assertEqual(self.request("/api/intervals/auth/init")[0], 404)
        self.assertEqual(self.request("/api/intervals/auth/init", "POST")[0], 401)
        code, _, body = self.request("/api/intervals/auth/init", "POST", "tok-okafor")
        self.assertEqual(code, 200)
        url = urllib.parse.urlsplit(body["authorize_url"])
        self.assertEqual(url.path, "/oauth/authorize")
        query = urllib.parse.parse_qs(url.query)
        self.assertEqual(query["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(server.verify_state(query["state"][0]), "u_okafor")

    def test_callback_connection_survives_time_and_rejects_mismatch(self):
        state = server.sign_state("u_okafor")
        token = {"access_token": "secret", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "Athlete"}}
        with patch.object(server, "exchange_code", return_value=token) as exchange:
            code, headers, _ = self.request("/api/intervals/callback?" + urllib.parse.urlencode(
                {"code": "abc", "state": state}))
            self.assertEqual(code, 302)
            self.assertEqual(headers["Location"], "/?connected=1")
            exchange.assert_called_once_with("abc")
        with patch.object(server.time, "time", return_value=server.time.time() + 7200):
            self.assertTrue(self.request("/api/intervals/status", token="tok-okafor")[2]["connected"])
        with patch.object(server, "exchange_code", return_value={**token,
                "athlete": {"id": "other", "name": "Other"}}):
            self.assertEqual(self.request("/api/intervals/callback?" + urllib.parse.urlencode(
                {"code": "def", "state": server.sign_state("u_okafor")}))[0], 409)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["athlete_id"], "i123")

    def test_revocation_clears_token_and_prompts_reconnect(self):
        server.store_connection("u_okafor", {"access_token": "secret",
            "athlete": {"id": "i123", "name": "Athlete"}})
        with patch.object(server, "intervals_get", return_value=(200, {"wellness": []})) as get:
            code, _, body = self.request("/api/intervals/wellness", token="tok-okafor")
        self.assertEqual((code, body), (200, {"wellness": []}))
        self.assertEqual(get.call_args.args[0]["access_token"], "secret")
        self.assertEqual(get.call_args.args[1], "/wellness")
        unauthorized = urllib.error.HTTPError("local", 401, "Unauthorized", {}, io.BytesIO())
        with patch.object(server, "intervals_get", side_effect=unauthorized):
            code, _, body = self.request("/api/intervals/wellness", token="tok-okafor")
        self.assertEqual(code, 409)
        self.assertIn("reconnect", body["error"])
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])
        self.assertFalse(self.request("/api/intervals/status", token="tok-okafor")[2]["connected"])

    def test_state_and_token_exchange_contract(self):
        state = server.sign_state("u_okafor")
        self.assertIsNone(server.verify_state(state[:-2] + "xx"))
        with patch.object(server.time, "time", return_value=server.time.time() + 901):
            self.assertIsNone(server.verify_state(state))
        with patch.object(server, "post_form", return_value={}) as post:
            server.exchange_code("abc")
        self.assertEqual(post.call_args.args[1], {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "abc"})


if __name__ == "__main__":
    unittest.main()
