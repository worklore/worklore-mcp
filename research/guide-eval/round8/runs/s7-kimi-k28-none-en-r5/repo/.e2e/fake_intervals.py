#!/usr/bin/env python3
"""Local stand-in for Intervals.icu, used only to test tricoach end-to-end.

Mimics the behavior documented in logs/ and the official OAuth docs:
- /oauth/authorize  -> 400 invalid_request for scopes the client is not
  registered for (CALENDAR:*), else 302 back with ?code=&state=
- /api/oauth/token  -> token WITHOUT expires_in and WITHOUT refresh_token
  (Intervals.icu access tokens do not expire; there is no refresh grant)
- /api/v1/athlete/{id}/wellness -> 200 JSON list
"""
import json, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VALID_SCOPES = {"ACTIVITY:READ", "ACTIVITY:WRITE", "WELLNESS:READ", "WELLNESS:WRITE",
                "SETTINGS:READ", "LIBRARY:READ", "LIBRARY:WRITE", "CHATS:READ"}
REGISTERED_FOR_CLIENT = {"ACTIVITY:READ", "ACTIVITY:WRITE", "WELLNESS:READ", "WELLNESS:WRITE"}
CODE = "fake-code-123"


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[fake-intervals]", fmt % args, flush=True)

    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        if url.path == "/oauth/authorize":
            q = dict(urllib.parse.parse_qsl(url.query))
            if q.get("client_id") != "tricoach-dev":
                return self.send_json(400, {"error": "invalid_request"})
            scopes = set(filter(None, (q.get("scope") or "").split(",")))
            if not scopes or not scopes.issubset(REGISTERED_FOR_CLIENT):
                # mirrors the captured production behavior
                return self.send_json(400, {"error": "invalid_request"})
            if q.get("response_type") not in (None, "code"):
                return self.send_json(400, {"error": "invalid_request"})
            back = q["redirect_uri"] + "?" + urllib.parse.urlencode(
                {"code": CODE, "state": q.get("state", "")})
            self.send_response(302)
            self.send_header("Location", back)
            self.end_headers()
            return
        if url.path.startswith("/api/v1/athlete/") and url.path.endswith("/wellness"):
            return self.send_json(200, [{"id": "2026-11-08", "weight": 70.2}])
        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        url = urllib.parse.urlsplit(self.path)
        if url.path == "/api/oauth/token":
            n = int(self.headers.get("Content-Length", 0))
            form = dict(urllib.parse.parse_qsl(self.rfile.read(n).decode()))
            if form.get("code") != CODE:
                return self.send_json(400, {"error": "invalid_grant"})
            # shape per the official docs example: no expires_in, no refresh_token
            return self.send_json(200, {
                "token_type": "Bearer",
                "access_token": "at-fake-0001",
                "scope": "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ",
                "athlete": {"id": "i12345", "name": "C. Okafor"},
            })
        self.send_json(404, {"error": "not found"})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8899), H).serve_forever()
