"""Local OAuth flow checks; all provider calls are replaced in process."""
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
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class IntervalsFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_port
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
        headers = {"Authorization": "Bearer " + token} if token else {}
        req = urllib.request.Request(self.base + path, method=method, headers=headers)
        try:
            response = urllib.request.build_opener(NoRedirect).open(req)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read()
            return response.status, json.loads(body) if body else {}, response.headers

    def test_connect_and_revocation(self):
        status, _, _ = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(status, 401)
        status, body, _ = self.request("/api/intervals/auth/init", "POST", "tok-okafor")
        self.assertEqual(status, 200)
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(body["authorize_url"]).query)
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        state = params["state"][0]
        self.assertEqual(server.verify_state(state), "u_okafor")
        with patch.object(server, "post_form", return_value={
            "access_token": "provider-token", "scope": config.SCOPES,
            "athlete": {"id": "i1", "name": "Athlete"},
        }) as exchange:
            callback = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "abc", "state": state})
            status, _, headers = self.request(callback)
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        self.assertEqual(exchange.call_args.args[1], {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "abc",
        })
        status, body, _ = self.request("/api/intervals/status", token="tok-okafor")
        self.assertTrue(body["connected"])
        with patch.object(server, "intervals_get", return_value=(200, [{"date": "2026-10-27"}])):
            status, body, _ = self.request("/api/intervals/wellness", token="tok-okafor")
        self.assertEqual((status, body), (200, [{"date": "2026-10-27"}]))
        with patch.object(server, "intervals_get", side_effect=urllib.error.HTTPError(
            "local", 401, "Unauthorized", {}, io.BytesIO(b""))):
            status, body, _ = self.request("/api/intervals/wellness", token="tok-okafor")
        self.assertEqual(status, 409)
        self.assertIn("reconnect", body["error"])
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])
        status, body, _ = self.request("/api/intervals/status", token="tok-okafor")
        self.assertFalse(body["connected"])

    def test_bad_state_and_account_mismatch(self):
        with patch.object(server, "post_form") as exchange:
            status, _, _ = self.request("/api/intervals/callback?code=x&state=invalid")
            self.assertEqual(status, 400)
            exchange.assert_not_called()
        server.store_connection("u_okafor", {"access_token": "old", "athlete": {"id": "i1"}})
        with patch.object(server, "post_form", return_value={
            "access_token": "new", "athlete": {"id": "i2"},
        }):
            callback = "/api/intervals/callback?" + urllib.parse.urlencode({
                "code": "abc", "state": server.sign_state("u_okafor"),
            })
            status, _, _ = self.request(callback)
        self.assertEqual(status, 409)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "old")


if __name__ == "__main__":
    unittest.main()
