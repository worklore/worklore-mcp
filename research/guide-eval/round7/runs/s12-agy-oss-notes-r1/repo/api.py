#!/usr/bin/env python3
"""tasks-api: the backend of a small social to-do app (Python standard library only).

    python3 api.py        # http://127.0.0.1:55228

Every request needs `Authorization: Bearer <token>`; the development tokens are in README.md.
A task is `private` (only its owner may see or touch it) or `public` (anyone may read, comment,
like, view and nudge; only the owner may edit, delete or complete it).
"""
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "55228"))

USERS = {  # token -> user id
    "tok_alice_4f8c2e71b0": "alice",
    "tok_bob_9a1d7c3e55": "bob",
}

TASKS = {}
NEXT_ID = [1]


def seed():
    """Reset the in-memory store to the development data."""
    TASKS.clear()
    NEXT_ID[0] = 1
    _add("alice", "Draft the investor update", "private")
    _add("alice", "Water the office plants", "public")
    _add("bob", "Book the team lunch", "public")


def _add(owner, title, visibility):
    tid = NEXT_ID[0]
    NEXT_ID[0] += 1
    TASKS[tid] = {"id": tid, "owner": owner, "title": title, "visibility": visibility,
                  "done": False, "likes": 0, "views": 0, "nudges": 0, "comments": []}
    return TASKS[tid]


# --- authorization helpers -------------------------------------------------

def can_access(user, task):
    """May `user` see this task at all? Public tasks: everyone. Private tasks: the owner only."""
    return task["visibility"] == "public" or task["owner"] == user


def is_owner(user, task):
    return task["owner"] == user


# --- HTTP ------------------------------------------------------------------

ROUTE = re.compile(r"^/tasks/(\d+)(?:/(comments|complete|nudge|like|view))?$")


class Handler(BaseHTTPRequestHandler):
    server_version = "tasks-api/0.3"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def user(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return USERS.get(auth[7:].strip())
        return None

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except ValueError:
            raise ValueError("body is not valid JSON")
        if not isinstance(data, dict):
            raise ValueError("body must be a JSON object")
        return data

    def dispatch(self, method):
        user = self.user()
        if user is None:
            return self.send(401, {"error": "missing or unknown bearer token"})
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        try:
            data = self.body() if method in ("POST", "PATCH") else {}
        except ValueError as e:
            return self.send(400, {"error": str(e)})

        if path == "/tasks" and method == "GET":
            mine = [t for t in TASKS.values() if can_access(user, t)]
            return self.send(200, {"tasks": mine})
        if path == "/tasks" and method == "POST":
            title = data.get("title")
            vis = data.get("visibility", "private")
            if not isinstance(title, str) or not title.strip():
                return self.send(400, {"error": "title is required"})
            if vis not in ("private", "public"):
                return self.send(400, {"error": "visibility must be private or public"})
            return self.send(201, _add(user, title.strip(), vis))

        m = ROUTE.match(path)
        if not m:
            return self.send(404, {"error": "no such route"})
        task = TASKS.get(int(m.group(1)))
        if task is None:
            return self.send(404, {"error": "no such task"})
        action = m.group(2)

        if action is None:
            if method == "GET":
                if not can_access(user, task):
                    return self.send(403, {"error": "forbidden"})
                return self.send(200, task)
            if method == "PATCH":
                if not is_owner(user, task):
                    return self.send(403, {"error": "only the owner may edit a task"})
                for k in ("title", "visibility"):
                    if k in data:
                        task[k] = data[k]
                return self.send(200, task)
            if method == "DELETE":
                if not is_owner(user, task):
                    return self.send(403, {"error": "only the owner may delete a task"})
                del TASKS[task["id"]]
                return self.send(200, {"deleted": task["id"]})
            return self.send(405, {"error": "method not allowed"})

        if method != "POST":
            return self.send(405, {"error": "method not allowed"})
        if action == "comments":
            if not can_access(user, task):
                return self.send(403, {"error": "forbidden"})
            text = data.get("text")
            if not isinstance(text, str) or not text.strip():
                return self.send(400, {"error": "text is required"})
            task["comments"].append({"by": user, "text": text.strip()})
            return self.send(201, task)
        if action == "complete":
            if not is_owner(user, task):
                return self.send(403, {"error": "only the owner may complete a task"})
            task["done"] = True
            return self.send(200, task)
        if action == "nudge":
            if not can_access(user, task):
                return self.send(403, {"error": "forbidden"})
            task["nudges"] += 1
            return self.send(200, {"id": task["id"], "nudges": task["nudges"]})
        if action == "like":
            if not can_access(user, task):
                return self.send(403, {"error": "forbidden"})
            task["likes"] += 1
            return self.send(200, {"id": task["id"], "likes": task["likes"]})
        if action == "view":
            if not can_access(user, task):
                return self.send(403, {"error": "forbidden"})
            task["views"] += 1
            return self.send(200, {"id": task["id"], "views": task["views"]})
        return self.send(404, {"error": "no such route"})

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def do_PATCH(self):
        self.dispatch("PATCH")

    def do_DELETE(self):
        self.dispatch("DELETE")


def make_server(port=PORT):
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    seed()
    srv = make_server()
    print("tasks-api listening on http://127.0.0.1:%d" % srv.server_address[1], flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
