import io
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

    def request(self, path, method="GET", auth=True):
        headers = {"Authorization": "Bearer tok-okafor"} if auth else {}
        req = urllib.request.Request(self.base + path, headers=headers, method=method)
        try:
            response = urllib.request.build_opener(NoRedirect).open(req)
        except urllib.error.HTTPError as e:
            response = e
        with response:
            return response.status, json.loads(response.read()) if response.headers.get_content_type() == "application/json" else response.headers["Location"]

    def test_init_requires_authenticated_post_and_uses_unique_scopes(self):
        self.assertEqual(self.request("/api/intervals/auth/init")[0], 404)
        self.assertEqual(self.request("/api/intervals/auth/init", "POST", auth=False)[0], 401)
        code, body = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(code, 200)
        url = urllib.parse.urlsplit(body["authorize_url"])
        self.assertEqual(url.path, "/oauth/authorize")
        params = urllib.parse.parse_qs(url.query)
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(params["redirect_uri"], [config.REDIRECT_URI])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

    def test_callback_token_exchange_and_revocation(self):
        _, init = self.request("/api/intervals/auth/init", "POST")
        state = urllib.parse.parse_qs(urllib.parse.urlsplit(init["authorize_url"]).query)["state"][0]
        token = {"access_token": "local-test-token", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "Okafor"}}
        fields_seen = []

        def fake_post(url, fields):
            fields_seen.append((url, fields))
            return token

        with patch.object(server, "post_form", side_effect=fake_post):
            code, location = self.request("/api/intervals/callback?" + urllib.parse.urlencode({"code": "abc", "state": state}), auth=False)
        self.assertEqual((code, location), (302, "/?connected=1"))
        self.assertEqual(fields_seen, [(server.TOKEN_URL, {"client_id": config.CLIENT_ID,
                                                        "client_secret": config.CLIENT_SECRET, "code": "abc"})])
        self.assertTrue(self.request("/api/intervals/status")[1]["connected"])
        with patch.object(server, "intervals_get", return_value=(200, [{"day": "today"}])):
            self.assertEqual(self.request("/api/intervals/wellness"), (200, [{"day": "today"}]))
        self.assertTrue(self.request("/api/intervals/status")[1]["connected"])
        unauthorized = urllib.error.HTTPError("local", 401, "Unauthorized", {}, io.BytesIO())
        with patch.object(server, "intervals_get", side_effect=unauthorized):
            self.assertEqual(self.request("/api/intervals/wellness")[0], 401)
        self.assertEqual(self.request("/api/intervals/status")[1]["status"], "reconnect required")
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])

    def test_invalid_state_and_other_athlete_do_not_replace_connection(self):
        token = {"access_token": "original", "athlete": {"id": "i123", "name": "Okafor"}}
        server.store_connection("u_okafor", token)
        self.assertEqual(self.request("/api/intervals/callback?code=abc&state=invalid", auth=False)[0], 400)
        state = server.sign_state("u_okafor")
        with patch.object(server, "post_form", return_value={"access_token": "other", "athlete": {"id": "i999"}}):
            code, _ = self.request("/api/intervals/callback?" + urllib.parse.urlencode({"code": "abc", "state": state}), auth=False)
        self.assertEqual(code, 409)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "original")


if __name__ == "__main__":
    unittest.main()
