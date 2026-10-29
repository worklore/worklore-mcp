#!/usr/bin/env python3
"""Local stand-in for intervals.icu OAuth + API, modelled on what the logs show.

- /oauth/authorize: rejects a scope list that names an area twice ("Duplicate scope"),
  otherwise redirects straight back to redirect_uri with a code (no consent screen).
- /api/oauth/token: needs client_id/client_secret/code; returns no refresh_token and no
  expires_in, like the real response in logs/connect-attempt.log.
- /api/v1/athlete/{id}/wellness: 401 for unknown or revoked tokens.
- /admin/revoke?token=...: revokes a token (simulates the athlete revoking the app).
"""
import json, secrets, sys, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CODES, TOKENS, REVOKED = {}, {}, set()
CLIENT = ("tricoach-dev", "s3cr3t-placeholder-0000")


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        sys.stderr.write("[mock] " + (a[0] % a[1:]) + "\n")

    def out(self, code, obj=None, loc=None):
        body = json.dumps(obj or {}).encode()
        self.send_response(code)
        if loc:
            self.send_header("Location", loc)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        if u.path == "/oauth/authorize":
            if q.get("client_id") != CLIENT[0] or not q.get("redirect_uri") or not q.get("state"):
                return self.out(400, {"error": "invalid_request"})
            areas = [s.split(":")[0] for s in q.get("scope", "").split(",")]
            if len(areas) != len(set(areas)):
                return self.out(400, {"error": "invalid_request", "message": "Duplicate scope"})
            code = secrets.token_urlsafe(8)
            CODES[code] = q["scope"]
            sep = "&" if "?" in q["redirect_uri"] else "?"
            return self.out(302, loc=f"{q['redirect_uri']}{sep}code={code}&state={urllib.parse.quote(q['state'])}")
        if u.path.startswith("/api/v1/athlete/"):
            auth = self.headers.get("Authorization", "")
            tok = auth[7:] if auth.startswith("Bearer ") else ""
            if tok not in TOKENS or tok in REVOKED:
                return self.out(401, {"error": "unauthorized"})
            return self.out(200, [{"id": "2026-10-20", "ctl": 42.0}])
        if u.path == "/admin/revoke":
            REVOKED.update(TOKENS if q.get("token") == "*" else {q.get("token", "")})
            return self.out(200, {"revoked": True})
        self.out(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        form = dict(urllib.parse.parse_qsl(self.rfile.read(n).decode()))
        if self.path == "/api/oauth/token":
            if (form.get("client_id"), form.get("client_secret")) != CLIENT or form.get("code") not in CODES:
                return self.out(400, {"error": "invalid_grant"})
            scope = CODES.pop(form["code"])
            tok = secrets.token_urlsafe(16)
            TOKENS[tok] = scope
            return self.out(200, {"token_type": "bearer", "access_token": tok, "scope": scope,
                                  "athlete": {"id": "i98765", "name": "T. Rivera"}})
        self.out(404, {"error": "not found"})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8800), H).serve_forever()
