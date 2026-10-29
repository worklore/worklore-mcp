"""Local HTTP checks for the Intervals connection flow; no provider calls."""
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


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.http.server_port}"
        cls.worker = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.worker.join()

    def setUp(self):
        with server.LOCK:
            server.CONNECTIONS.clear()

    def request(self, path, method="GET", token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, method=method, headers=headers)
        try:
            response = urllib.request.build_opener(NoRedirect).open(req)
        except urllib.error.HTTPError as e:
            response = e
        with response:
            body = response.read()
            return response.code, json.loads(body) if body else {}, response.headers

    def init(self, token="tok-okafor"):
        code, body, _ = self.request("/api/intervals/auth/init", "POST", token)
        self.assertEqual(code, 200)
        return urllib.parse.parse_qs(urllib.parse.urlsplit(body["authorize_url"]).query)

    def test_init_requires_authenticated_post_and_unique_scope_areas(self):
        self.assertEqual(self.request("/api/intervals/auth/init")[0], 404)
        self.assertEqual(self.request("/api/intervals/auth/init", "POST")[0], 401)
        params = self.init()
        self.assertEqual(params["scope"], [config.SCOPES])
        areas = [scope.split(":")[0] for scope in params["scope"][0].split(",")]
        self.assertEqual(len(areas), len(set(areas)))
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")
        self.assertIsNone(server.verify_state("broken"))

    def test_callback_connection_persists_and_revocation_requests_reconnect(self):
        state = self.init()["state"][0]
        tok = {"access_token": "access-1", "scope": config.SCOPES,
               "athlete": {"id": "i123", "name": "Athlete"}}
        with patch.object(server, "exchange_code", return_value=tok) as exchange:
            code, _, headers = self.request("/api/intervals/callback?" +
                urllib.parse.urlencode({"code": "abc", "state": state}))
        self.assertEqual(code, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        exchange.assert_called_once_with("abc")
        self.assertEqual(self.request("/api/intervals/status", token="tok-okafor")[1]["connected"], True)
        with patch.object(server, "intervals_get", return_value=(200, [{"date": "2026-10-27"}])):
            self.assertEqual(self.request("/api/intervals/wellness", token="tok-okafor")[0], 200)
        revoked = urllib.error.HTTPError("local", 401, "Unauthorized", {}, io.BytesIO())
        with patch.object(server, "intervals_get", side_effect=revoked):
            self.assertEqual(self.request("/api/intervals/wellness", token="tok-okafor")[0], 409)
        revoked.close()
        status = self.request("/api/intervals/status", token="tok-okafor")[1]
        self.assertFalse(status["connected"])
        self.assertEqual(status["status"], "revoked, reconnect")
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])

    def test_reconnect_rejects_different_athlete(self):
        first = {"access_token": "first", "athlete": {"id": "i123"}}
        other = {"access_token": "other", "athlete": {"id": "i456"}}
        server.store_connection("u_okafor", first)
        state = self.init()["state"][0]
        with patch.object(server, "exchange_code", return_value=other):
            code, _, _ = self.request("/api/intervals/callback?" +
                urllib.parse.urlencode({"code": "abc", "state": state}))
        self.assertEqual(code, 409)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["athlete_id"], "i123")

    def test_token_exchange_uses_intervals_fields_only(self):
        with patch.object(server, "post_form", return_value={"access_token": "access"}) as post:
            server.exchange_code("abc")
        post.assert_called_once_with(server.TOKEN_URL, {
            "client_id": config.CLIENT_ID,
            "client_secret": config.CLIENT_SECRET,
            "code": "abc",
        })


if __name__ == "__main__":
    unittest.main()
