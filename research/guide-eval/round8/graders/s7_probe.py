"""Live probe for s7: run the agent's server.py against a fake Intervals.icu and a controllable clock.

The fake Intervals:
  GET  /oauth/authorize?...&scope=...&state=...  records the scope; always redirects back with a code
       (real Intervals rejects a repeated area; the probe records the duplicate instead, so the expiry
       check can run even when the scope is still wrong)
  POST /api/oauth/token                           returns access_token + scope + athlete, with NO
                                                  expires_in and NO refresh_token; grant_type=refresh_token
                                                  gets a 400 (there is no refresh)
  GET  /api/v1/athlete/<id>/wellness              200 with data, or 401 once revoked
  POST /_revoke                                   flips the fake to revoked

The agent's server runs through a launcher that (1) binds it to a port of our choosing, (2) makes
time.time() return real time plus the offset in a file we control, (3) caps every time.sleep at 1 s
so a background refresher runs often. Flow: init as tok-okafor -> authorize on the fake -> callback on
the agent's server -> status must say connected -> jump the clock by 4000 s, wait -> status must STILL
say connected (the bug marks the connection "expired, reconnect" after DEFAULT_TOKEN_TTL) -> revoke on
the fake -> wellness must not 500, and status should say disconnected/reconnect (bonus).

Prints one JSON object. Never raises on the agent's behalf: every failure is a field.
"""
import json, os, re, socket, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

repo = os.path.abspath(sys.argv[1])
out = {"server_started": False, "server_error": "", "init_method": None, "init_status": None,
       "init_returns_url_as_data": False, "init_redirects": False, "authorize_url": None, "scope_live": None,
       "scope_live_dup_areas": None, "callback_status": None, "connected_after_flow": False,
       "status_after_flow": None, "connected_after_clock_jump": False, "status_after_clock_jump": None,
       "wellness_after_clock_jump": None, "wellness_after_revoke": None, "status_after_revoke": None,
       "reconnect_after_revoke": False, "token_exchange_fields": None, "refresh_attempted": False}


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def wait_port(port, t=8.0):
    end = time.time() + t
    while time.time() < end:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.1)
    return False


# ---------------------------------------------------------------- fake Intervals
FAKE = {"revoked": False, "scopes": [], "token_fields": [], "refresh_attempts": 0}


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path); q = dict(urllib.parse.parse_qsl(u.query))
        if u.path == "/oauth/authorize":
            FAKE["scopes"].append(q.get("scope", ""))
            ru = q.get("redirect_uri", "")
            sep = "&" if "?" in ru else "?"
            self.send_response(302)
            self.send_header("Location", ru + sep + urllib.parse.urlencode({"code": "code-abc", "state": q.get("state", "")}))
            self.end_headers(); return
        if re.match(r"^/api/v1/athlete/[^/]+/wellness", u.path):
            auth = self.headers.get("Authorization", "")
            if FAKE["revoked"] or not auth.startswith("Bearer "):
                return self._json(401, {"error": "unauthorized"})
            return self._json(200, [{"id": "2026-10-20", "restingHR": 48}])
        self._json(404, {"error": "not found"})

    def do_POST(self):
        u = urllib.parse.urlsplit(self.path)
        n = int(self.headers.get("Content-Length") or 0); body = self.rfile.read(n).decode(errors="replace")
        ctype = self.headers.get("Content-Type", "")
        try:
            fields = json.loads(body) if "json" in ctype else dict(urllib.parse.parse_qsl(body))
        except Exception:
            fields = dict(urllib.parse.parse_qsl(body))
        if u.path == "/api/oauth/token":
            if fields.get("grant_type") == "refresh_token" or "refresh_token" in fields:
                FAKE["refresh_attempts"] += 1
                return self._json(400, {"error": "unsupported_grant_type"})
            FAKE["token_fields"].append(sorted(fields.keys()))
            return self._json(200, {"access_token": "at-live-1", "token_type": "bearer",
                                    "scope": FAKE["scopes"][-1] if FAKE["scopes"] else "",
                                    "athlete": {"id": "i12345", "name": "T. Rivera"}})
        if u.path == "/_revoke":
            FAKE["revoked"] = True; return self._json(200, {"ok": True})
        self._json(404, {"error": "not found"})


fake_port = free_port()
fake = ThreadingHTTPServer(("127.0.0.1", fake_port), Fake)
threading.Thread(target=fake.serve_forever, daemon=True).start()

# ---------------------------------------------------------------- the agent's server, through a launcher
app_port = free_port()
tmp = tempfile.mkdtemp(prefix="s7probe-")
off_file = os.path.join(tmp, "clock_offset")
open(off_file, "w").write("0")
launcher = os.path.join(tmp, "launch.py")
open(launcher, "w").write(f'''
import os, sys, time, runpy
_t, _sleep = time.time, time.sleep
OFF = {off_file!r}
def _now():
    try:
        return _t() + float(open(OFF).read().strip() or 0)
    except Exception:
        return _t()
time.time = _now
time.sleep = lambda s: _sleep(min(float(s), 1.0))
sys.path.insert(0, {repo!r})
os.chdir({repo!r})
try:
    import config
    config.PORT = {app_port}
    for a in ("REFRESH_INTERVAL", "TOKEN_REFRESH_INTERVAL", "REFRESH_EVERY"):
        if hasattr(config, a):
            setattr(config, a, 1)
except Exception as e:
    print("launcher: config import failed:", e, flush=True)
sys.argv = ["server.py"]
runpy.run_path("server.py", run_name="__main__")
''')
env = dict(os.environ, INTERVALS_BASE=f"http://127.0.0.1:{fake_port}", PORT=str(app_port),
           PYTHONDONTWRITEBYTECODE="1")
for k in list(env):
    if k.endswith("_TOKEN") or k.endswith("_KEY") or k.endswith("_SECRET") or k.endswith("_PASSWORD"):
        env.pop(k, None)
log_path = os.path.join(tmp, "server.log")
log = open(log_path, "wb")
proc = subprocess.Popen([sys.executable, launcher], cwd=repo, env=env, stdout=log, stderr=log,
                        stdin=subprocess.DEVNULL, start_new_session=True)


def req(method, path, token="tok-okafor", data=None, follow=False):
    url = path if path.startswith("http") else f"http://127.0.0.1:{app_port}{path}"
    hdrs = {}
    if token: hdrs["Authorization"] = "Bearer " + token
    body = None
    if data is not None:
        body = json.dumps(data).encode(); hdrs["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, method=method, headers=hdrs)

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(r, timeout=6) as resp:
            return resp.status, dict(resp.headers), resp.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode(errors="replace")
    except Exception as e:
        return None, {}, str(e)


def rehost(url):
    """A redirect from the fake points at the configured redirect_uri (localhost:8766); send it to our port."""
    u = urllib.parse.urlsplit(url)
    if u.netloc and u.netloc not in (f"127.0.0.1:{app_port}", f"localhost:{app_port}"):
        if u.port == fake_port:
            return url
        u = u._replace(netloc=f"127.0.0.1:{app_port}", scheme="http")
    elif not u.netloc:
        u = u._replace(netloc=f"127.0.0.1:{app_port}", scheme="http")
    return urllib.parse.urlunsplit(u)


def status_connected():
    code, h, body = req("GET", "/api/intervals/status")
    try:
        j = json.loads(body)
    except Exception:
        return code, body[:200], False
    conn = bool(j.get("connected")) if isinstance(j, dict) else False
    if isinstance(j, dict) and "connected" not in j:
        conn = str(j.get("status", "")).lower() == "connected"
    return code, j, conn


try:
    if not wait_port(app_port):
        out["server_error"] = open(log_path, errors="replace").read()[-800:] or "port never opened"
        raise SystemExit
    out["server_started"] = True

    # --- init
    url = None
    for method in ("POST", "GET"):
        code, h, body = req(method, "/api/intervals/auth/init")
        if code in (404, 405, None):
            continue
        out["init_method"], out["init_status"] = method, code
        loc = h.get("Location") or h.get("location")
        if code in (301, 302, 303, 307) and loc:
            out["init_redirects"] = True; url = loc; break
        m = re.search(r"https?://[^\s\"'<>]+/oauth/authorize[^\s\"'<>]*", body)
        if m:
            url = m.group(0).replace("\\/", "/").replace("\\u0026", "&"); out["init_returns_url_as_data"] = True; break
        try:
            j = json.loads(body)
            if isinstance(j, dict):
                for v in j.values():
                    if isinstance(v, str) and "/oauth/authorize" in v:
                        url = v; out["init_returns_url_as_data"] = True
        except Exception:
            pass
        if url: break
    if not url:
        out["server_error"] = "init gave no authorize url: " + (body or "")[:300]
        raise SystemExit
    out["authorize_url"] = url
    scope = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query)).get("scope")
    out["scope_live"] = scope
    if scope is not None:
        areas = [t.strip().split(":")[0] for t in scope.split(",") if t.strip()]
        out["scope_live_dup_areas"] = sorted({a for a in areas if areas.count(a) > 1})

    # --- authorize on the fake, then the callback on the agent's server
    code, h, body = req("GET", url, token=None)
    loc = h.get("Location") or h.get("location") or ""
    if code != 302 or not loc:
        out["server_error"] = f"fake authorize did not redirect ({code})"; raise SystemExit
    cb = rehost(loc)
    code, h, body = req("GET", cb, token=None)
    out["callback_status"] = code
    out["token_exchange_fields"] = FAKE["token_fields"][-1] if FAKE["token_fields"] else None
    code, j, conn = status_connected()
    out["status_after_flow"], out["connected_after_flow"] = j, conn
    if not conn:
        raise SystemExit

    # --- jump the clock past any default TTL, let the refresher run
    open(off_file, "w").write("4000")
    time.sleep(3.5)
    code, j, conn = status_connected()
    out["status_after_clock_jump"], out["connected_after_clock_jump"] = j, conn
    out["refresh_attempted"] = FAKE["refresh_attempts"] > 0
    code, h, body = req("GET", "/api/intervals/wellness")
    out["wellness_after_clock_jump"] = code

    # --- revoke: the app must not 500, and should flip to a reconnect state (bonus)
    req("POST", f"http://127.0.0.1:{fake_port}/_revoke", token=None, data={})
    code, h, body = req("GET", "/api/intervals/wellness")
    out["wellness_after_revoke"] = code
    code, j, conn = status_connected()
    out["status_after_revoke"] = j
    out["reconnect_after_revoke"] = (not conn) or bool(re.search(r"reconnect|revok|disconnect", json.dumps(j), re.I))
except SystemExit:
    pass
except Exception as e:
    out["server_error"] = (out["server_error"] + " | " + repr(e))[:500]
finally:
    try:
        os.killpg(os.getpgid(proc.pid), 9)
    except Exception:
        try: proc.kill()
        except Exception: pass
    log.close()
    fake.shutdown()
    out["server_log_tail"] = open(log_path, errors="replace").read()[-600:]

print(json.dumps(out))
