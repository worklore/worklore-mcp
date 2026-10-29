"""Local end-to-end checks for the Intervals connection flow."""
import json
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import server


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class IntegrationTest(unittest.TestCase):
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
        server.CONNECTIONS.clear()

    def request(self, path, method="GET", token=None, redirects=True):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, headers=headers, method=method)
        opener = urllib.request.build_opener() if redirects else urllib.request.build_opener(NoRedirect)
        try:
            response = opener.open(req)
        except urllib.error.HTTPError as e:
            response = e
        with response:
            data = response.read()
            return response.code, json.loads(data) if data else {}, response.headers

    def test_connection_revocation_and_reconnect_identity(self):
        code, _, _ = self.request("/api/intervals/auth/init", token="tok-okafor")
        self.assertEqual(code, 404)  # only POST can initiate OAuth
        code, _, _ = self.request("/api/intervals/auth/init", method="POST")
        self.assertEqual(code, 401)
        code, result, _ = self.request("/api/intervals/auth/init", method="POST", token="tok-okafor")
        self.assertEqual(code, 200)
        authorize = urllib.parse.urlsplit(result["authorize_url"])
        params = urllib.parse.parse_qs(authorize.query)
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        state = params["state"][0]

        token_response = {"access_token": "test-intervals-token", "scope": params["scope"][0],
                          "athlete": {"id": "i123", "name": "C. Okafor"}}
        with patch.object(server, "post_form", return_value=token_response) as exchange:
            code, _, headers = self.request("/api/intervals/callback?" + urllib.parse.urlencode(
                {"code": "auth-code", "state": state}), redirects=False)
        self.assertEqual(code, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        self.assertEqual(exchange.call_args.args[1], {
            "client_id": server.config.CLIENT_ID, "client_secret": server.config.CLIENT_SECRET, "code": "auth-code"})
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "test-intervals-token")
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])

        code, result, _ = self.request("/api/intervals/status", token="tok-okafor")
        self.assertEqual((code, result["connected"]), (200, True))
        with patch.object(server, "intervals_get", return_value=(200, [{"date": "2026-10-26"}])):
            code, result, _ = self.request("/api/intervals/wellness", token="tok-okafor")
        self.assertEqual((code, result), (200, [{"date": "2026-10-26"}]))

        revoked = urllib.error.HTTPError("https://intervals.icu", 401, "Unauthorized", {}, None)
        with patch.object(server, "intervals_get", side_effect=revoked):
            code, result, _ = self.request("/api/intervals/wellness", token="tok-okafor")
        revoked.close()
        self.assertEqual(code, 409)
        self.assertIn("reconnect", result["error"])
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])
        code, result, _ = self.request("/api/intervals/status", token="tok-okafor")
        self.assertFalse(result["connected"])

        other = {**token_response, "athlete": {"id": "other", "name": "Other"}}
        with patch.object(server, "post_form", return_value=other):
            code, _, _ = self.request("/api/intervals/callback?" + urllib.parse.urlencode(
                {"code": "auth-code-2", "state": state}))
        self.assertEqual(code, 409)
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])

    def test_invalid_state_is_rejected_before_exchange(self):
        with patch.object(server, "post_form") as exchange:
            code, _, _ = self.request("/api/intervals/callback?code=x&state=bad")
        self.assertEqual(code, 400)
        exchange.assert_not_called()
        with patch.object(server.time, "time", return_value=1000):
            state = server.sign_state("u_okafor")
        self.assertIsNone(server.verify_state(state))


if __name__ == "__main__":
    unittest.main()
