import http.client
import json
import threading
import unittest
import urllib.error
import urllib.parse
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import config
import server


class OAuthFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def setUp(self):
        server.CONNECTIONS.clear()

    def request(self, method, path, token=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port)
        headers = {"Authorization": "Bearer " + token} if token else {}
        conn.request(method, path, headers=headers)
        response = conn.getresponse()
        body = response.read()
        result = response.status, dict(response.getheaders()), json.loads(body) if body else None
        conn.close()
        return result

    def test_connect_callback_and_revocation(self):
        self.assertEqual(self.request("GET", "/api/intervals/auth/init")[0], 404)
        self.assertEqual(self.request("POST", "/api/intervals/auth/init")[0], 401)
        status, _, body = self.request("POST", "/api/intervals/auth/init", "tok-okafor")
        self.assertEqual(status, 200)
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(body["authorize_url"]).query)
        self.assertEqual(params["scope"], [config.SCOPES])
        self.assertEqual(len({s.split(":")[0] for s in config.SCOPES.split(",")}), 3)

        token = {"access_token": "secret", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "Athlete"}}
        with patch.object(server, "post_form", return_value=token) as post:
            status, headers, _ = self.request("GET", "/api/intervals/callback?" +
                urllib.parse.urlencode({"code": "abc", "state": params["state"][0]}))
        self.assertEqual((status, headers["Location"]), (302, "/?connected=1"))
        post.assert_called_once_with(server.TOKEN_URL, {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "abc"})
        self.assertEqual(self.request("GET", "/api/intervals/status", "tok-okafor")[2]["connected"], True)
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])

        revoked = urllib.error.HTTPError("mock", 401, "Unauthorized", {}, None)
        with patch.object(server, "intervals_get", side_effect=revoked):
            self.assertEqual(self.request("GET", "/api/intervals/wellness", "tok-okafor")[0], 409)
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])
        self.assertEqual(self.request("GET", "/api/intervals/status", "tok-okafor")[2]["connected"], False)

    def test_invalid_state_and_mismatched_athlete(self):
        self.assertEqual(self.request("GET", "/api/intervals/callback?code=x&state=bad")[0], 400)
        server.store_connection("u_rivera", {"access_token": "old", "athlete": {"id": "i1"}})
        with patch.object(server, "exchange_code", return_value={"access_token": "new", "athlete": {"id": "i2"}}):
            status, _, _ = self.request("GET", "/api/intervals/callback?" +
                urllib.parse.urlencode({"code": "x", "state": server.sign_state("u_rivera")}))
        self.assertEqual(status, 409)
        self.assertEqual(server.CONNECTIONS["u_rivera"]["access_token"], "old")


if __name__ == "__main__":
    unittest.main()
