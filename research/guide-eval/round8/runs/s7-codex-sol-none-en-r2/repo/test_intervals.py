import json
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

import config
import server


class IntervalsTests(unittest.TestCase):
    def setUp(self):
        server.CONNECTIONS.clear()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.httpd.server_port}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()
        server.CONNECTIONS.clear()

    def request(self, path, token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return urllib.request.urlopen(urllib.request.Request(self.base + path, headers=headers))

    def test_connect_requires_auth_and_returns_valid_scopes(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/api/intervals/auth/init")
        self.assertEqual(error.exception.code, 401)
        error.exception.close()

        with self.request("/api/intervals/auth/init", "tok-okafor") as response:
            self.assertEqual(response.status, 200)
            url = json.load(response)["authorize_url"]
        parsed = urllib.parse.urlsplit(url)
        params = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(parsed.path, "/oauth/authorize")
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(params["redirect_uri"], [config.REDIRECT_URI])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

    def test_token_without_expiry_stays_connected_and_can_fetch_wellness(self):
        tok = {"access_token": "provider-token", "scope": config.SCOPES,
               "athlete": {"id": "i98765", "name": "T. Rivera"}}
        state = server.sign_state("u_rivera")
        with mock.patch.object(server, "exchange_code", return_value=tok):
            with self.request("/api/intervals/callback?" + urllib.parse.urlencode({"code": "abc", "state": state})) as response:
                self.assertEqual(response.status, 200)  # urllib follows the local redirect
        connection = server.CONNECTIONS["u_rivera"]
        self.assertIsNone(connection["expires_at"])
        with mock.patch.object(server, "post_form", side_effect=AssertionError("unexpected refresh")):
            with mock.patch.object(server.time, "time", return_value=server.time.time() + 7200):
                server.refresh_connections()
        self.assertEqual(connection["status"], "connected")
        self.assertEqual(connection["access_token"], "provider-token")
        with mock.patch.object(server, "intervals_get", return_value=(200, [{"wellness": True}])):
            with self.request("/api/intervals/wellness", "tok-rivera") as response:
                self.assertEqual(json.load(response), [{"wellness": True}])

    def test_provider_401_requires_reconnect(self):
        server.store_connection("u_okafor", {"access_token": "revoked", "athlete": {"id": "i1"}})
        provider_error = urllib.error.HTTPError("https://intervals.icu", 401, "Unauthorized", {}, None)
        with mock.patch.object(server, "intervals_get", side_effect=provider_error):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request("/api/intervals/wellness", "tok-okafor")
        self.assertEqual(error.exception.code, 401)
        error.exception.close()
        with self.request("/api/intervals/status", "tok-okafor") as response:
            self.assertEqual(json.load(response), {"connected": False, "status": "expired, reconnect"})


if __name__ == "__main__":
    unittest.main()
