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


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class IntervalsFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

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
        req = urllib.request.Request(self.base + path, headers=headers, method=method)
        opener = urllib.request.build_opener(NoRedirect)
        try:
            with opener.open(req) as response:
                return response.status, response.headers, response.read()
        except urllib.error.HTTPError as e:
            with e:
                return e.code, e.headers, e.read()

    def test_init_callback_wellness_and_revocation(self):
        status, _, body = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(status, 401)
        status, _, body = self.request("/api/intervals/auth/init", "POST", "tok-okafor")
        self.assertEqual(status, 200)
        authorize_url = json.loads(body)["authorize_url"]
        params = urllib.parse.parse_qs(urllib.parse.urlsplit(authorize_url).query)
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")
        callback = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "local-code", "state": params["state"][0]})
        token_response = {"access_token": "local-token", "scope": config.SCOPES,
                          "athlete": {"id": "i123", "name": "C. Okafor"}}
        with patch.object(server, "post_form", return_value=token_response) as exchange:
            status, headers, _ = self.request(callback)
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        self.assertEqual(exchange.call_args.args[1], {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "local-code"})
        status, _, body = self.request("/api/intervals/status", token="tok-okafor")
        self.assertTrue(json.loads(body)["connected"])
        with patch.object(server, "intervals_get", return_value=(200, [{"date": "2026-10-27"}])) as get:
            status, _, body = self.request("/api/intervals/wellness", token="tok-okafor")
        self.assertEqual(status, 200)
        self.assertEqual(get.call_args.args[0]["access_token"], "local-token")
        self.assertEqual(json.loads(body), [{"date": "2026-10-27"}])
        with patch.object(server, "intervals_get", side_effect=urllib.error.HTTPError("local", 401, "revoked", {}, None)):
            status, _, _ = self.request("/api/intervals/wellness", token="tok-okafor")
        self.assertEqual(status, 409)
        status, _, body = self.request("/api/intervals/status", token="tok-okafor")
        self.assertFalse(json.loads(body)["connected"])
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])

    def test_bad_state_and_mismatched_athlete(self):
        status, _, _ = self.request("/api/intervals/callback?code=x&state=bad")
        self.assertEqual(status, 400)
        server.store_connection("u_rivera", {"access_token": "original", "athlete": {"id": "i1"}})
        with self.assertRaises(ValueError):
            server.store_connection("u_rivera", {"access_token": "replacement", "athlete": {"id": "i2"}})
        self.assertEqual(server.CONNECTIONS["u_rivera"]["access_token"], "original")


if __name__ == "__main__":
    unittest.main()
