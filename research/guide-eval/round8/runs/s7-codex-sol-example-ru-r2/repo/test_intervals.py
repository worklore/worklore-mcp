"""Local HTTP checks for the Intervals connection flow; no network provider calls."""
import http.client
import json
import threading
import time
import unittest
import urllib.error
import urllib.parse
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import config
import server


class ConnectionFlowTests(unittest.TestCase):
    def setUp(self):
        server.CONNECTIONS.clear()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()
        server.CONNECTIONS.clear()

    def request(self, method, path, token=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port)
        headers = {"Authorization": "Bearer " + token} if token else {}
        conn.request(method, path, headers=headers)
        response = conn.getresponse()
        body = response.read()
        result = response.status, dict(response.getheaders()), json.loads(body) if body else None
        conn.close()
        return result

    def test_connect_persists_and_revocation_requires_reconnect(self):
        self.assertEqual(self.request("GET", "/api/intervals/auth/init", "tok-okafor")[0], 404)
        self.assertEqual(self.request("POST", "/api/intervals/auth/init")[0], 401)
        code, _, body = self.request("POST", "/api/intervals/auth/init", "tok-okafor")
        self.assertEqual(code, 200)
        url = urllib.parse.urlsplit(body["authorize_url"])
        params = dict(urllib.parse.parse_qsl(url.query))
        self.assertEqual(params["scope"], "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE")
        self.assertEqual(server.verify_state(params["state"]), "u_okafor")
        self.assertIsNone(server.verify_state(params["state"] + "x"))

        token = {"access_token": "provider-token", "scope": params["scope"],
                 "athlete": {"id": "i123", "name": "C. Okafor"}}
        callback = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "abc", "state": params["state"]})
        with patch.object(server, "post_form", return_value=token) as post:
            self.assertEqual(self.request("GET", callback)[0], 302)
            post.assert_called_once_with(server.TOKEN_URL, {
                "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "abc"})
        self.assertEqual(self.request("GET", "/api/intervals/status", "tok-okafor")[2]["connected"], True)
        self.assertNotIn("expires_at", server.CONNECTIONS["u_okafor"])
        self.assertNotIn("refresh_token", server.CONNECTIONS["u_okafor"])

        with patch.object(server, "intervals_get", return_value=(200, [{"date": "2026-10-27"}])):
            self.assertEqual(self.request("GET", "/api/intervals/wellness", "tok-okafor")[0], 200)
        with patch.object(server, "intervals_get", side_effect=urllib.error.HTTPError("url", 401, "", {}, None)):
            self.assertEqual(self.request("GET", "/api/intervals/wellness", "tok-okafor")[0], 409)
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["access_token"])
        self.assertEqual(self.request("GET", "/api/intervals/status", "tok-okafor")[2]["connected"], False)

    def test_reconnect_rejects_different_athlete(self):
        server.CONNECTIONS["u_okafor"] = {"athlete_id": "i123", "athlete_name": "C. Okafor",
                                           "access_token": None, "scope": None, "status": "reconnect required"}
        state = server.sign_state("u_okafor")
        callback = "/api/intervals/callback?" + urllib.parse.urlencode({"code": "abc", "state": state})
        token = {"access_token": "other-token", "athlete": {"id": "i999"}}
        with patch.object(server, "post_form", return_value=token):
            self.assertEqual(self.request("GET", callback)[0], 409)
        self.assertEqual(server.CONNECTIONS["u_okafor"]["athlete_id"], "i123")

    def test_state_expires_and_rejects_wrong_purpose(self):
        with patch.object(server.time, "time", return_value=1000):
            state = server.sign_state("u_okafor")
        with patch.object(server.time, "time", return_value=1901):
            self.assertIsNone(server.verify_state(state))
        with patch.object(server.time, "time", return_value=1000):
            self.assertEqual(server.verify_state(state), "u_okafor")
        # A valid signature with a different purpose must still fail.
        import base64
        import hashlib
        import hmac
        payload = base64.urlsafe_b64encode(json.dumps({
            "sub": "u_okafor", "purpose": "other", "iat": int(time.time())}).encode()).decode().rstrip("=")
        sig = hmac.new(config.APP_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        self.assertIsNone(server.verify_state(payload + "." + sig))


if __name__ == "__main__":
    unittest.main()
