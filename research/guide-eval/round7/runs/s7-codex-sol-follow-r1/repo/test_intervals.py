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


class IntervalsTests(unittest.TestCase):
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
        server.CONNECTIONS.clear()

    def request(self, path, method="GET", token="tok-okafor"):
        headers = {"Authorization": "Bearer " + token} if token else {}
        req = urllib.request.Request(self.base + path, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            with error:
                return error.code, json.load(error)

    def test_init_requires_post_auth_and_unique_scopes(self):
        self.assertEqual(self.request("/api/intervals/auth/init")[0], 404)
        self.assertEqual(self.request("/api/intervals/auth/init", "POST", None)[0], 401)
        status, body = self.request("/api/intervals/auth/init", "POST")
        self.assertEqual(status, 200)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(body["authorize_url"]).query)
        self.assertEqual(query["scope"], [config.SCOPES])
        self.assertEqual(server.verify_state(query["state"][0]), "u_okafor")

    def test_token_exchange_fields_and_encryption(self):
        with patch.object(server, "post_form", return_value={"access_token": "secret", "athlete": {"id": "123"}}) as post:
            tok = server.exchange_code("code")
        self.assertEqual(post.call_args.args[1], {
            "client_id": config.CLIENT_ID, "client_secret": config.CLIENT_SECRET, "code": "code"})
        server.store_connection("u_okafor", tok)
        self.assertNotIn("secret", repr(server.CONNECTIONS["u_okafor"]))
        self.assertEqual(server.TOKEN_CIPHER.decrypt(server.CONNECTIONS["u_okafor"]["encrypted_token"]).decode(), "secret")

    def test_account_mismatch_preserves_connection(self):
        server.store_connection("u_okafor", {"access_token": "first", "athlete": {"id": "123"}})
        with self.assertRaisesRegex(ValueError, "does not match"):
            server.store_connection("u_okafor", {"access_token": "second", "athlete": {"id": "456"}})
        self.assertEqual(server.CONNECTIONS["u_okafor"]["athlete_id"], "123")

    def test_provider_401_prompts_reconnect(self):
        server.store_connection("u_okafor", {"access_token": "secret", "athlete": {"id": "123"}})
        error = urllib.error.HTTPError("url", 401, "Unauthorized", {}, None)
        with patch.object(server, "intervals_get", side_effect=error):
            status, body = self.request("/api/intervals/wellness")
        self.assertEqual(status, 409)
        self.assertIn("reconnect", body["error"])
        self.assertIsNone(server.CONNECTIONS["u_okafor"]["encrypted_token"])
        self.assertEqual(self.request("/api/intervals/status")[1]["status"], "reconnect")

    def test_state_rejects_wrong_purpose_and_expiry(self):
        with patch.object(server.time, "time", return_value=1000):
            state = server.sign_state("u_okafor")
        with patch.object(server.time, "time", return_value=1900):
            self.assertIsNone(server.verify_state(state))
        self.assertIsNone(server.verify_state(state + "x"))
        header, payload, _ = state.split(".")
        wrong = {"sub": "u_okafor", "purpose": "other", "exp": 2000}
        encoded = server.base64.urlsafe_b64encode(json.dumps(wrong).encode()).decode().rstrip("=")
        message = header + "." + encoded
        signature = server.hmac.new(config.APP_SECRET.encode(), message.encode(), server.hashlib.sha256).digest()
        bad_purpose = message + "." + server.base64.urlsafe_b64encode(signature).decode().rstrip("=")
        with patch.object(server.time, "time", return_value=1000):
            self.assertIsNone(server.verify_state(bad_purpose))


if __name__ == "__main__":
    unittest.main()
