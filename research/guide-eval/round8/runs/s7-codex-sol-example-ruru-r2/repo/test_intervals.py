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
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class IntervalsFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.http.server_port}"

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
        req = urllib.request.Request(self.base + path, data=b"" if method == "POST" else None,
                                     headers=headers, method=method)
        try:
            response = urllib.request.build_opener(NoRedirect).open(req)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            body = response.read()
            return response.status, json.loads(body) if response.headers.get_content_type() == "application/json" and body else None, response.headers

    def test_init_requires_authenticated_post_and_unique_scopes(self):
        self.assertEqual(self.request("/api/intervals/auth/init")[0], 404)
        self.assertEqual(self.request("/api/intervals/auth/init", "POST")[0], 401)
        code, body, _ = self.request("/api/intervals/auth/init", "POST", "tok-okafor")
        self.assertEqual(code, 200)
        url = urllib.parse.urlsplit(body["authorize_url"])
        self.assertEqual(url.scheme, "https")
        params = urllib.parse.parse_qs(url.query)
        self.assertEqual(params["scope"], ["ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"])
        self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")

    def test_code_exchange_uses_provider_fields_only(self):
        with patch.object(server, "post_form", return_value={}) as post:
            server.exchange_code("some-code")
        post.assert_called_once_with(server.TOKEN_URL, {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "some-code"
        })

    def test_callback_connects_without_expiry_and_revocation_requires_reconnect(self):
        state = server.sign_state("u_okafor")
        token = {"access_token": "intervals-token", "scope": config.SCOPES,
                 "athlete": {"id": "i123", "name": "C. Okafor"}}
        with patch.object(server, "exchange_code", return_value=token) as exchange:
            code, _, headers = self.request("/api/intervals/callback?" + urllib.parse.urlencode({
                "code": "some-code", "state": state
            }))
        self.assertEqual(code, 302)
        self.assertEqual(headers["Location"], "/?connected=1")
        exchange.assert_called_once_with("some-code")
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])
        self.assertEqual(self.request("/api/intervals/status", token="tok-okafor")[1]["connected"], True)

        unauthorized = urllib.error.HTTPError("local", 401, "Unauthorized", {}, io.BytesIO())
        with patch.object(server, "intervals_get", side_effect=unauthorized):
            self.assertEqual(self.request("/api/intervals/wellness", token="tok-okafor")[0], 401)
        unauthorized.close()
        self.assertEqual(self.request("/api/intervals/status", token="tok-okafor")[1],
                         {"connected": False, "status": "reconnect required"})
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])

    def test_rejects_different_athlete_on_reconnect(self):
        server.store_connection("u_okafor", {"access_token": "old", "athlete": {"id": "i123"}})
        other = {"access_token": "new", "athlete": {"id": "i456"}}
        with patch.object(server, "exchange_code", return_value=other):
            code, _, _ = self.request("/api/intervals/callback?" + urllib.parse.urlencode({
                "code": "other-code", "state": server.sign_state("u_okafor")
            }))
        self.assertEqual(code, 409)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["access_token"], "old")

    def test_rejects_expired_or_modified_state(self):
        state = server.sign_state("u_okafor")
        self.assertIsNone(server.verify_state(state, max_age=-1))
        self.assertIsNone(server.verify_state(state[:-3] + "xxx"))


if __name__ == "__main__":
    unittest.main()
