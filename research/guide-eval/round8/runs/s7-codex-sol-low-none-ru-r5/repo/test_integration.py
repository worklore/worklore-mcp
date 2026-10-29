import json
import threading
import unittest
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

import config
import server


class IntegrationTests(unittest.TestCase):
    def test_authorize_init_uses_authenticated_api_request(self):
        http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{http.server_port}/api/intervals/auth/init"
            req = urllib.request.Request(url, headers={"Authorization": "Bearer tok-okafor"})
            with urllib.request.urlopen(req) as response:
                self.assertEqual(response.status, 200)
                target = json.load(response)["authorize_url"]
            params = urllib.parse.parse_qs(urllib.parse.urlsplit(target).query)
            self.assertEqual(params["scope"], [config.SCOPES])
            self.assertEqual(server.verify_state(params["state"][0]), "u_okafor")
            self.assertNotIn("CALENDAR:", params["scope"][0])
        finally:
            http.shutdown()
            http.server_close()
            thread.join()

    def test_token_without_expiry_stays_connected(self):
        server.store_connection("u_rivera", {
            "access_token": "example", "scope": "WELLNESS:READ",
            "athlete": {"id": "i98765", "name": "T. Rivera"},
        })
        connection = server.CONNECTIONS["u_rivera"]
        self.assertIsNone(connection["expires_at"])
        self.assertEqual(connection["status"], "connected")


if __name__ == "__main__":
    unittest.main()
