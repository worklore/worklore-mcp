import io
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


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class IntervalsFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.http.server_port}"
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.opener = urllib.request.build_opener(NoRedirect)

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()

    def setUp(self):
        with server.LOCK:
            server.CONNECTIONS.clear()

    def request(self, path, method="GET", token=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        req = urllib.request.Request(self.base + path, headers=headers, method=method)
        try:
            response = self.opener.open(req)
        except urllib.error.HTTPError as e:
            response = e
        with response:
            body = response.read()
            return response.code, response.headers, json.loads(body) if body else None

    def test_init_callback_and_revocation(self):
        code, _, _ = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(code, 401)
        code, _, _ = self.request("/api/intervals/auth/init", "GET", "tok-okafor")
        self.assertEqual(code, 404)
        code, _, body = self.request("/api/intervals/auth/init", "POST", "tok-okafor")
        self.assertEqual(code, 200)
        authorize = urllib.parse.urlsplit(body["authorize_url"])
        params = urllib.parse.parse_qs(authorize.query)
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

        callback = "/api/intervals/callback?" + urllib.parse.urlencode(
            {"state": params["state"][0], "code": "example-code"})
        tok = {"access_token": "example-token", "scope": config.SCOPES,
               "athlete": {"id": "i123", "name": "C. Okafor"}}
        with patch.object(server, "exchange_code", return_value=tok) as exchange:
            code, headers, _ = self.request(callback)
        self.assertEqual(code, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        exchange.assert_called_once_with("example-code")
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])
        with patch.object(server.time, "time", return_value=time.time() + 7200):
            code, _, body = self.request("/api/intervals/status", token="tok-okafor")
        self.assertTrue(body["connected"])
        with patch.object(server, "intervals_get", return_value=(200, [{"date": "2026-10-27"}])) as get:
            code, _, body = self.request("/api/intervals/wellness", token="tok-okafor")
        self.assertEqual((code, body), (200, [{"date": "2026-10-27"}]))
        self.assertEqual(get.call_args.args[0]["athlete_id"], "i123")

        revoked = urllib.error.HTTPError("mock", 401, "Unauthorized", {}, io.BytesIO())
        with patch.object(server, "intervals_get", side_effect=revoked):
            code, _, body = self.request("/api/intervals/wellness", token="tok-okafor")
        revoked.close()
        self.assertEqual(code, 409)
        self.assertIn("reconnect", body["error"])
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])
        _, _, body = self.request("/api/intervals/status", token="tok-okafor")
        self.assertEqual(body, {"connected": False, "status": "reconnect"})

        other = dict(tok, athlete={"id": "i999", "name": "Other"})
        with patch.object(server, "exchange_code", return_value=other):
            code, _, body = self.request(callback)
        self.assertEqual(code, 409)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["athlete_id"], "i123")

    def test_exchange_fields_and_state_validation(self):
        with patch.object(server, "post_form", return_value={}) as post:
            server.exchange_code("code")
        self.assertEqual(post.call_args.args[1], {"client_id": config.CLIENT_ID,
                         "client_secret": config.CLIENT_SECRET, "code": "code"})
        with patch.object(server.time, "time", return_value=1000):
            state = server.sign_state("u_rivera")
        with patch.object(server.time, "time", return_value=1901):
            self.assertIsNone(server.verify_state(state))
        with patch.object(server.time, "time", return_value=999):
            self.assertIsNone(server.verify_state(state))
        self.assertIsNone(server.verify_state("invalid-state"))


if __name__ == "__main__":
    unittest.main()
