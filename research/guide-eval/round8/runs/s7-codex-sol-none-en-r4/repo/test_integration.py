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


class IntervalsFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join()

    def setUp(self):
        with server.LOCK:
            server.CONNECTIONS.clear()

    def request(self, path, method="GET", token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, data=b"" if method == "POST" else None,
                                     headers=headers, method=method)
        return urllib.request.urlopen(req)

    def test_authenticated_connect_and_indefinite_token(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/api/intervals/auth/init", method="POST")
        self.assertEqual(error.exception.code, 401)
        error.exception.close()

        with self.request("/api/intervals/auth/init", method="POST", token="tok-okafor") as response:
            authorize_url = json.load(response)["authorize_url"]
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(authorize_url).query)
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(params["redirect_uri"], [config.REDIRECT_URI])

        token_response = {"access_token": "provider-token", "scope": params["scope"][0],
                          "athlete": {"id": "i123", "name": "Athlete"}}
        callback = "/api/intervals/callback?" + urllib.parse.urlencode(
            {"code": "test-code", "state": params["state"][0]})
        with patch.object(server, "exchange_code", return_value=token_response) as exchange:
            with self.request(callback) as response:
                self.assertEqual(response.geturl(), self.base + "/?connected=1")
            exchange.assert_called_once_with("test-code")
        with server.LOCK:
            connection = server.CONNECTIONS["u_okafor"].copy()
        self.assertEqual(connection["access_token"], "provider-token")
        self.assertNotIn("expires_at", connection)
        self.assertNotIn("refresh_token", connection)
        with self.request("/api/intervals/status", token="tok-okafor") as response:
            self.assertTrue(json.load(response)["connected"])

    def test_code_exchange_uses_provider_form_fields(self):
        with patch.object(server, "post_form", return_value={}) as post:
            server.exchange_code("test-code")
        post.assert_called_once_with(server.TOKEN_URL, {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET,
            "code": "test-code",
        })

    def test_provider_rejection_prompts_reconnect(self):
        server.store_connection("u_rivera", {"access_token": "revoked", "scope": "WELLNESS:READ",
                                              "athlete": {"id": "i456", "name": "Rivera"}})
        error = urllib.error.HTTPError("provider", 401, "Unauthorized", {}, None)
        with patch.object(server, "intervals_get", side_effect=error):
            with self.assertRaises(urllib.error.HTTPError) as response:
                self.request("/api/intervals/wellness", token="tok-rivera")
        self.assertEqual(response.exception.code, 401)
        response.exception.close()
        with self.request("/api/intervals/status", token="tok-rivera") as response:
            self.assertEqual(json.load(response), {"connected": False, "status": "reconnect"})


if __name__ == "__main__":
    unittest.main()
