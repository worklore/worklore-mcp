import json
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import config
import server


class ConnectionTests(unittest.TestCase):
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

    def get(self, path, token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        request = urllib.request.Request(self.base + path, headers=headers)
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_auth_init_requires_token_and_returns_known_good_scopes(self):
        status, body = self.get("/api/intervals/auth/init")
        self.assertEqual(status, 401)
        self.assertEqual(body["error"], "unauthorized")

        status, body = self.get("/api/intervals/auth/init", "tok-okafor")
        self.assertEqual(status, 200)
        url = urllib.parse.urlsplit(body["authorize_url"])
        params = urllib.parse.parse_qs(url.query)
        self.assertEqual(url.path, "/oauth/authorize")
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ"])
        self.assertEqual(params["redirect_uri"], [config.REDIRECT_URI])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

    def test_callback_token_without_expiry_stays_connected(self):
        token = {"access_token": "fake-access", "scope": config.SCOPES,
                 "athlete": {"id": "i98765", "name": "T. Rivera"}}
        state = server.sign_state("u_rivera")
        path = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "fake-code", "state": state})
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, request, response, code, message, headers, url):
                return None

        opener = urllib.request.build_opener(NoRedirect)
        with patch.object(server, "exchange_code", return_value=token):
            # The callback does not need a tricoach Authorization header.
            with self.assertRaises(urllib.error.HTTPError) as result:
                opener.open(self.base + path)
            self.assertEqual(result.exception.code, 302)
            self.assertEqual(result.exception.headers["Location"], "/?connected=1")
            result.exception.close()

        self.assertIsNone(server.CONNECTIONS["u_rivera"]["expires_at"])
        with patch.object(server, "post_form", side_effect=AssertionError("unexpected refresh")):
            server.refresh_tokens_once()
        status, body = self.get("/api/intervals/status", "tok-rivera")
        self.assertEqual(status, 200)
        self.assertTrue(body["connected"])
        self.assertEqual(body["athlete"]["id"], "i98765")

    def test_explicit_expiry_is_honored(self):
        server.store_connection("u_okafor", {"access_token": "short", "expires_in": 120,
                                             "athlete": {"id": "i1"}})
        server.refresh_tokens_once()
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "connected")
        server.CONNECTIONS["u_okafor"]["expires_at"] = time.time() - 1
        server.refresh_tokens_once()
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "expired, reconnect")

    def test_refreshable_token_is_renewed(self):
        server.store_connection("u_okafor", {"access_token": "old", "refresh_token": "refresh",
                                             "expires_in": 120, "athlete": {"id": "i1"}})
        with patch.object(server, "post_form", return_value={"access_token": "new",
                                                            "expires_in": 3600}) as post:
            server.refresh_tokens_once()
        self.assertEqual(post.call_args.args[1]["grant_type"], "refresh_token")
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "new")
        self.assertEqual(server.CONNECTIONS["u_okafor"]["refresh_token"], "refresh")


if __name__ == "__main__":
    unittest.main()
