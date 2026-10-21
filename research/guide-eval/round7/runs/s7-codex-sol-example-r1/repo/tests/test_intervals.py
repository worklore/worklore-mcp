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


class IntervalsFlowTests(unittest.TestCase):
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

    def request(self, path, method="GET", auth=True):
        headers = {"Authorization": "Bearer tok-okafor"} if auth else {}
        req = urllib.request.Request(self.base + path, headers=headers, method=method)
        opener = urllib.request.build_opener(NoRedirect)
        try:
            with opener.open(req) as res:
                return res.status, dict(res.headers), res.read()
        except urllib.error.HTTPError as e:
            with e:
                return e.code, dict(e.headers), e.read()

    def authorize(self):
        code, _, body = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(code, 200)
        url = json.loads(body)["authorize_url"]
        return urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)

    def test_init_requires_spa_auth_and_has_unique_scope_areas(self):
        self.assertEqual(self.request("/api/intervals/auth/init", "POST", False)[0], 401)
        self.assertEqual(self.request("/api/intervals/auth/init")[0], 404)
        params = self.authorize()
        self.assertEqual(params["scope"], [config.SCOPES])
        self.assertEqual(len({s.split(":")[0] for s in config.SCOPES.split(",")}), 3)
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")
        self.assertIsNone(server.verify_state(params["state"][0][:-2] + "xx"))

    def test_callback_exchanges_only_supported_fields_and_keeps_token(self):
        state = self.authorize()["state"][0]
        token = {"access_token": "access-1", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "C. Okafor"}}
        with patch.object(server, "post_form", return_value=token) as post:
            path = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "auth-code", "state": state})
            code, headers, _ = self.request(path, auth=False)
        self.assertEqual(code, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        post.assert_called_once_with(server.TOKEN_URL, {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "auth-code"})
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "access-1")
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])
        self.assertEqual(json.loads(self.request("/api/intervals/status")[2])["connected"], True)

    def test_revoked_token_prompts_reconnect_and_preserves_account_guard(self):
        server.store_connection("u_okafor", {"access_token": "access-1",
                                "athlete": {"id": "i123", "name": "C. Okafor"}})
        unauthorized = urllib.error.HTTPError("url", 401, "Unauthorized", {}, io.BytesIO())
        with patch.object(server, "intervals_get", side_effect=unauthorized):
            self.assertEqual(self.request("/api/intervals/wellness")[0], 409)
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])
        self.assertEqual(json.loads(self.request("/api/intervals/status")[2])["status"], "reconnect")
        with self.assertRaisesRegex(ValueError, "differs"):
            server.store_connection("u_okafor", {"access_token": "other",
                                    "athlete": {"id": "i999"}})
        server.store_connection("u_okafor", {"access_token": "access-2",
                                "athlete": {"id": "i123"}})
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "connected")


if __name__ == "__main__":
    unittest.main()
