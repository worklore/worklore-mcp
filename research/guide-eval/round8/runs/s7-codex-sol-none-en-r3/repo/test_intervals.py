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

    def request(self, path, method="GET", token="tok-okafor"):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, headers=headers, method=method)
        try:
            with urllib.request.build_opener(NoRedirect).open(req) as response:
                return response.status, response.headers, response.read()
        except urllib.error.HTTPError as error:
            try:
                return error.code, error.headers, error.read()
            finally:
                error.close()

    def test_authenticated_init_and_callback_without_refresh_token(self):
        code, _, body = self.request("/api/intervals/auth/init", method="POST", token=None)
        self.assertEqual(code, 401)
        code, _, body = self.request("/api/intervals/auth/init")
        self.assertEqual(code, 404)

        code, _, body = self.request("/api/intervals/auth/init", method="POST")
        self.assertEqual(code, 200)
        auth_url = json.loads(body)["authorize_url"]
        parsed = urllib.parse.urlsplit(auth_url)
        self.assertEqual(parsed.path, "/oauth/authorize")
        params = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(params["scope"], [config.SCOPES])
        areas = [scope.split(":")[0] for scope in config.SCOPES.split(",")]
        self.assertEqual(len(areas), len(set(areas)))
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

        token_response = {
            "access_token": "provider-token", "scope": config.SCOPES,
            "athlete": {"id": "i123", "name": "Athlete"},
        }
        callback = "/api/intervals/callback?" + urllib.parse.urlencode(
            {"code": "sample-code", "state": params["state"][0]})
        with patch.object(server, "post_form", return_value=token_response) as post:
            code, headers, _ = self.request(callback, token=None)
        self.assertEqual(code, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        post.assert_called_once_with(server.TOKEN_URL, {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET,
            "code": "sample-code",
        })
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "provider-token")
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])
        code, _, body = self.request("/api/intervals/status")
        self.assertEqual(code, 200)
        self.assertTrue(json.loads(body)["connected"])

    def test_revoked_token_requires_reconnect(self):
        server.store_connection("u_okafor", {
            "access_token": "revoked", "scope": "WELLNESS:READ",
            "athlete": {"id": "i123", "name": "Athlete"},
        })
        error = urllib.error.HTTPError("https://intervals.icu/", 401, "", {}, None)
        with patch.object(server, "intervals_get", side_effect=error):
            code, _, _ = self.request("/api/intervals/wellness")
        self.assertEqual(code, 401)
        code, _, body = self.request("/api/intervals/status")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["status"], "reconnect required")
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])


if __name__ == "__main__":
    unittest.main()
