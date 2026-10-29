import http.client
import json
import threading
import time
import unittest
import urllib.error
import urllib.parse
from unittest.mock import patch

import config
import server


class IntervalsConnectionTests(unittest.TestCase):
    def setUp(self):
        server.CONNECTIONS.clear()
        self.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()
        server.CONNECTIONS.clear()

    def request(self, path, token=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port)
        headers = {"Authorization": "Bearer " + token} if token else {}
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        data = response.read()
        status = response.status
        conn.close()
        return status, json.loads(data) if data else None

    def test_authorized_start_and_durable_token_survives_refresh_pass(self):
        self.assertEqual(self.request("/api/intervals/auth/init")[0], 401)
        status, body = self.request("/api/intervals/auth/init", "tok-rivera")
        self.assertEqual(status, 200)
        url = urllib.parse.urlsplit(body["authorize_url"])
        self.assertEqual(url.path, "/oauth/authorize")
        params = urllib.parse.parse_qs(url.query)
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ"])
        self.assertEqual(params["redirect_uri"], [config.REDIRECT_URI])
        self.assertEqual(server.verify_state(params["state"][0]), "u_rivera")

        token = {"access_token": "durable-token", "scope": params["scope"][0],
                 "athlete": {"id": "i98765", "name": "T. Rivera"}}
        callback = "/api/intervals/callback?" + urllib.parse.urlencode(
            {"code": "sample-code", "state": params["state"][0]})
        with patch.object(server, "exchange_code", return_value=token):
            conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port)
            conn.request("GET", callback)
            response = conn.getresponse()
            self.assertEqual(response.status, 302)
            self.assertEqual(response.getheader("Location"), "/?connected=1")
            response.read()
            conn.close()

        with patch.object(server, "post_form") as post_form:
            server.refresh_due_connections(now=time.time() + 7200)
            post_form.assert_not_called()
        self.assertIsNone(server.CONNECTIONS["u_rivera"]["expires_at"])
        status, body = self.request("/api/intervals/status", "tok-rivera")
        self.assertEqual(status, 200)
        self.assertTrue(body["connected"])

    def test_explicit_expiry_without_refresh_token_waits_until_expiry(self):
        server.store_connection("u_okafor", {
            "access_token": "short-lived", "expires_in": 3600,
            "athlete": {"id": "i123", "name": "C. Okafor"},
        })
        expiry = server.CONNECTIONS["u_okafor"]["expires_at"]
        server.refresh_due_connections(now=expiry - 200)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "connected")
        server.refresh_due_connections(now=expiry + 1)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "expired, reconnect")

    def test_refresh_of_expiring_token(self):
        server.store_connection("u_okafor", {
            "access_token": "old", "refresh_token": "refresh-me", "expires_in": 60,
        })
        with patch.object(server, "post_form", return_value={
            "access_token": "new", "expires_in": 3600,
        }) as post_form:
            server.refresh_due_connections()
        self.assertEqual(post_form.call_count, 1)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "new")
        self.assertEqual(server.CONNECTIONS["u_okafor"]["refresh_token"], "refresh-me")

    def test_temporary_refresh_failure_keeps_unexpired_token(self):
        server.store_connection("u_okafor", {
            "access_token": "still-valid", "refresh_token": "refresh-me", "expires_in": 240,
        })
        with patch.object(server, "post_form", side_effect=OSError("temporary failure")):
            server.refresh_due_connections()
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "connected")
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "still-valid")

    def test_provider_unauthorized_marks_connection_for_reconnect(self):
        server.store_connection("u_okafor", {
            "access_token": "revoked", "athlete": {"id": "i123"},
        })
        error = urllib.error.HTTPError("https://intervals.icu", 401, "Unauthorized", {}, None)
        with patch.object(server, "intervals_get", side_effect=error):
            status, _ = self.request("/api/intervals/wellness", "tok-okafor")
        self.assertEqual(status, 401)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["status"], "expired, reconnect")


if __name__ == "__main__":
    unittest.main()
