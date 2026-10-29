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


class IntervalsConnectionTests(unittest.TestCase):
    def setUp(self):
        server.CONNECTIONS.clear()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.worker = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.worker.start()
        self.base = f"http://127.0.0.1:{self.httpd.server_port}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.worker.join()
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

    def test_auth_init_requires_app_token_and_returns_valid_authorize_url(self):
        code, body = self.get("/api/intervals/auth/init")
        self.assertEqual(code, 401)
        self.assertEqual(body["error"], "unauthorized")

        code, body = self.get("/api/intervals/auth/init", "tok-okafor")
        self.assertEqual(code, 200)
        url = urllib.parse.urlsplit(body["authorize_url"])
        params = dict(urllib.parse.parse_qsl(url.query))
        self.assertEqual(url.path, "/oauth/authorize")
        self.assertEqual(params["scope"], "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ")
        self.assertEqual(params["redirect_uri"], config.REDIRECT_URI)
        self.assertEqual(server.verify_state(params["state"]), "u_okafor")

    def test_callback_keeps_token_without_provider_expiry(self):
        token_response = {
            "access_token": "provider-token", "scope": "ACTIVITY:WRITE,WELLNESS:READ",
            "athlete": {"id": "i98765", "name": "T. Rivera"},
        }
        state = server.sign_state("u_rivera")
        callback = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "sample-code", "state": state})
        with patch.object(server, "exchange_code", return_value=token_response):
            request = urllib.request.Request(self.base + callback)
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, request, fp, code, msg, headers, url):
                    return None

            opener = urllib.request.build_opener(NoRedirect)
            with self.assertRaises(urllib.error.HTTPError) as result:
                opener.open(request)
            with result.exception as response:
                self.assertEqual(response.code, 302)

        connection = server.CONNECTIONS["u_rivera"]
        self.assertIsNone(connection["expires_at"])
        with patch.object(server, "post_form", side_effect=AssertionError("unexpected refresh")):
            server.refresh_due_tokens()
        self.assertEqual(connection["status"], "connected")
        code, body = self.get("/api/intervals/status", "tok-rivera")
        self.assertEqual(code, 200)
        self.assertTrue(body["connected"])

    def test_refresh_only_expires_a_token_at_its_actual_deadline(self):
        server.store_connection("u_okafor", {
            "access_token": "expiring-token", "expires_in": 240,
            "athlete": {"id": "i123"},
        })
        connection = server.CONNECTIONS["u_okafor"]
        server.refresh_due_tokens()
        self.assertEqual(connection["status"], "connected")
        connection["expires_at"] = 0
        server.refresh_due_tokens()
        self.assertEqual(connection["status"], "expired, reconnect")


if __name__ == "__main__":
    unittest.main()
