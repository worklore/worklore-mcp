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
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.http.server_port}"

    def tearDown(self):
        self.http.shutdown()
        self.thread.join()
        self.http.server_close()
        server.CONNECTIONS.clear()

    def get(self, path, token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, headers=headers)
        with urllib.request.urlopen(req) as response:
            return json.load(response)

    def test_auth_init_requires_app_token_and_returns_valid_authorize_url(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get("/api/intervals/auth/init")
        self.assertEqual(error.exception.code, 401)
        error.exception.close()

        data = self.get("/api/intervals/auth/init", "tok-okafor")
        url = urllib.parse.urlsplit(data["url"])
        query = urllib.parse.parse_qs(url.query)
        self.assertEqual(url.path, "/oauth/authorize")
        self.assertEqual(query["scope"], [config.SCOPES])
        self.assertNotIn("CALENDAR:", query["scope"][0])
        self.assertIn("WELLNESS:READ", query["scope"][0])
        self.assertEqual(server.verify_state(query["state"][0]), "u_okafor")

    def test_callback_keeps_token_without_provider_expiry_connected(self):
        state = server.sign_state("u_rivera")
        token = {"access_token": "provider-token", "scope": "ACTIVITY:WRITE,WELLNESS:READ",
                 "athlete": {"id": "i98765", "name": "T. Rivera"}}
        with patch.object(server, "exchange_code", return_value=token):
            req = urllib.request.Request(self.base + "/api/intervals/callback?" +
                                         urllib.parse.urlencode({"code": "test-code", "state": state}))
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, request, fp, code, msg, headers, newurl):
                    return None

            with self.assertRaises(urllib.error.HTTPError) as response:
                urllib.request.build_opener(NoRedirect()).open(req)
            self.assertEqual(response.exception.code, 302)
            self.assertEqual(response.exception.headers["Location"], "/?connected=1")
            response.exception.close()
        self.assertIsNone(server.CONNECTIONS["u_rivera"]["expires_at"])
        with patch.object(server, "post_form") as post:
            server.refresh_tokens_once(now=server.time.time() + 86400)
            post.assert_not_called()
        status = self.get("/api/intervals/status", "tok-rivera")
        self.assertTrue(status["connected"])
        self.assertEqual(status["athlete"]["id"], "i98765")

    def test_provider_expiry_without_refresh_token_expires(self):
        server.store_connection("u_okafor", {"access_token": "short-lived", "expires_in": 60})
        server.refresh_tokens_once(now=server.time.time() + 61)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "expired, reconnect")

    def test_provider_unauthorized_marks_connection_for_reconnect(self):
        server.store_connection("u_okafor", {"access_token": "revoked"})
        failure = urllib.error.HTTPError("https://intervals.icu/api/v1/athlete/x/wellness",
                                         401, "Unauthorized", {}, None)
        with patch.object(server, "intervals_get", side_effect=failure):
            with self.assertRaises(urllib.error.HTTPError) as response:
                self.get("/api/intervals/wellness", "tok-okafor")
            self.assertEqual(response.exception.code, 401)
            response.exception.close()
        self.assertEqual(self.get("/api/intervals/status", "tok-okafor")["status"],
                         "expired, reconnect")


if __name__ == "__main__":
    unittest.main()
