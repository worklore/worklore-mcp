"""s7: Intervals.icu OAuth quirks. Hidden answer key (three planted problems, all in the fixture code):
  1. scope lists an area twice (ACTIVITY:READ,ACTIVITY:WRITE,...,CALENDAR:READ,CALENDAR:WRITE). Intervals
     rejects a repeated area; :WRITE implies :READ. Fix: each area at most once. (Dropping :READ where the
     same area has :WRITE is a bonus, not required.)
  2. the token exchange assumes refresh_token / expires_in, stores an expiry, and a background
     refresh_tokens() pass marks the connection "expired, reconnect" after an hour. Intervals tokens have
     neither: they live until revoked. Fix: no expiry, no refresh machinery (401-driven reconnect is a bonus).
  3. the Connect button is a plain <a href="/api/intervals/auth/init"> (GET navigation: no Authorization
     header -> 401). Fix: init is an authenticated POST (or at least fetched) returning the authorize URL,
     and the frontend navigates to it (window.location.assign / href = variable).
PASS = scope_fixed AND no_expiry_assumed AND init_fixed, where the first two come from a LIVE probe
(s7_probe.py): the agent's server.py runs against a fake Intervals that returns tokens with no expires_in
and no refresh_token, the probe walks init -> authorize -> callback as tok-okafor, reads the scope off the
authorize URL it was handed, then jumps the server's clock by 4000 s and asks the status endpoint again.
scope_fixed = no area repeated in the live scope (static scan as fallback when the flow never started);
no_expiry_assumed = still connected after the clock jump (the bug marks it "expired, reconnect");
init_fixed = no bare link in the JS, the JS fetches init and navigates to a variable, and init answered
with the authorize URL as data (JSON/text) rather than a redirect.
The identifier scan (refresh/expiry names left in the code) is kept as information only: an agent that
keeps a generic refresher but schedules no expiry when the provider sends none has fixed the bug.
ANSWER.md is only used for "causes named", which is recorded but not required.
"""
import ast, io, json, os, re, sys, tokenize
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R)
txt = run_text(R)

SKIP_DIRS = {".git", "logs", "node_modules", "__pycache__", "notes"}

def files(exts):
    out = []
    for d, dirs, fs in os.walk(repo):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in fs:
            if f.endswith(exts) and not f.lower().startswith("test"):
                out.append(os.path.join(d, f))
    return sorted(out)

def strip_py(src, strings=False):
    """Python source without comments and docstrings; with strings=True also without string contents."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    lines = src.splitlines(keepends=True)
    def blank(node):
        for i in range(node.lineno - 1, node.end_lineno):
            lines[i] = "\n"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body \
                and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Constant) \
                and isinstance(node.body[0].value.value, str):
            blank(node.body[0])
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO("".join(lines)).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if strings and tok.type == tokenize.STRING:
                out.append((tok.type, '""'))
            elif strings and tok.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
                out.append((tok.type, ""))
            else:
                out.append((tok.type, tok.string))
        return tokenize.untokenize(out)
    except (tokenize.TokenError, IndentationError):
        return "".join(lines)

def strip_js(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(?<![:\\])//[^\n]*", "", src)

# --- 1. scope ---------------------------------------------------------------------------------------
TOK = r"[A-Z][A-Z_]*:(?:READ|WRITE)"
SCOPE_RE = re.compile(rf"(?<![A-Z_:]){TOK}(?:\s*,\s*{TOK})*(?![A-Z_:])")

def scope_candidates():
    """Every scope string the code could send: whole-string literals, scope=... inside a literal, lists of tokens."""
    found = []
    for p in files((".py",)):
        try:
            tree = ast.parse(read(p))
        except SyntaxError:
            found.append(("<syntax error> " + os.path.relpath(p, repo), None)); continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value.strip()
                m = SCOPE_RE.fullmatch(s) or re.search(rf"scope=({SCOPE_RE.pattern})", s)
                if m:
                    found.append((os.path.relpath(p, repo), m.group(1) if m.lastindex else m.group(0)))
            elif isinstance(node, (ast.List, ast.Tuple, ast.Set)) and node.elts and all(
                    isinstance(e, ast.Constant) and isinstance(e.value, str) and re.fullmatch(TOK, e.value.strip()) for e in node.elts):
                found.append((os.path.relpath(p, repo), ",".join(e.value.strip() for e in node.elts)))
    return found

def scope_problems(s):
    toks = [t.strip() for t in s.split(",")]
    areas = [t.split(":")[0] for t in toks]
    dup = sorted({a for a in areas if areas.count(a) > 1})
    read_and_write = sorted({a for a in areas if f"{a}:READ" in toks and f"{a}:WRITE" in toks})
    return dup, read_and_write

cands = scope_candidates()
scope_strings = [s for _, s in cands if s]
scope_dups = sorted({a for s in scope_strings for a in scope_problems(s)[0]})
scope_fixed = bool(scope_strings) and not scope_dups and not any(s is None for _, s in cands)
scope_no_read_with_write = scope_fixed and not any(scope_problems(s)[1] for s in scope_strings)

# --- 2. refresh / expiry machinery ------------------------------------------------------------------
py_sources = {os.path.relpath(p, repo): read(p) for p in files((".py",)) if os.path.basename(p) != "config.py"}
server_src = read(os.path.join(repo, "server.py"))
idents_refresh, idents_expiry, parse_errors = set(), set(), []
for name, src in py_sources.items():
    s2 = strip_py(src, strings=True)
    if s2 is None:
        parse_errors.append(name); continue
    for ident in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", s2):
        low = ident.lower()
        if "refresh" in low: idents_refresh.add(ident)
        if "state" in low or low == "ttl": continue  # the state JWT's TTL is the story's step 3, not a token expiry
        if "expir" in low or low in ("token_ttl",) or low.endswith("_ttl"): idents_expiry.add(ident)
# An optional `refresh_token` read or field is tolerated (the story says there is none, but keeping the
# field costs nothing); what must go is the refresh JOB and any expiry: identifiers like refresh_tokens,
# refresh_all, refresh_loop, do_refresh, and anything with "expir" or a TTL.
idents_refresh_job = {i for i in idents_refresh if i.lower() not in ("refresh_token", "refresh_tokens_present", "has_refresh_token", "refresh_token_present")
                      and not i.lower().startswith("refresh_token_")}
refresh_expiry_removed = not parse_errors and bool(py_sources) and not idents_refresh_job and not idents_expiry
s1_server = strip_py(server_src) or ""
reconnect_on_401 = bool(re.search(r"(?:code|status|status_code|reason)\s*==\s*401\b|\b401\s*==|in\s*\(\s*401|case\s+401", s1_server)) \
    and bool(re.search(r"revok|reconnect|disconnect", s1_server, re.I))

# --- 3. init endpoint: POST + fetch + navigate -----------------------------------------------------
js = "\n".join(strip_js(read(p)) for p in files((".js", ".html")))
bare_get_link = bool(re.search(r"""href\s*=\s*["'`][^"'`]*auth/init""", js)) or \
    bool(re.search(r"""location(?:\.href)?\s*=\s*["'`][^"'`]*auth/init|location\.(?:assign|replace)\(\s*["'`][^"'`]*auth/init""", js)) or \
    bool(re.search(r"""action\s*=\s*["'`][^"'`]*auth/init""", js))
js_fetches_init = bool(re.search(r"""(?<![\w.])(?!assign|replace|open)\w+\(\s*["'`][^"'`\n]*auth/init""", js)) or \
    (bool(re.search(r"""["'`][^"'`\n]*auth/init["'`]""", js)) and not bare_get_link and "fetch(" in js)
js_posts_init = js_fetches_init and bool(re.search(r"""method\s*:\s*["'`]POST["'`]""", js, re.I))
# navigation to something computed (a variable, a property, an awaited call), not to a string literal
js_navigates = bool(re.search(r"""location\.(?:assign|replace)\(\s*[^"'`\s)][^)]*\)|(?:location\.href|window\.location|location)\s*=\s*[^"'`\s;=][^;\n]*""", js))

def init_route_methods():
    """Where '/api/intervals/auth/init' (or any 'auth/init') appears in the Python: inside do_POST / do_GET,
    or next to a 'POST' / 'GET' literal in a routing tuple or call. Returns {'POST', 'GET'} subsets."""
    methods = set()
    for p in files((".py",)):
        try:
            tree = ast.parse(read(p))
        except SyntaxError:
            continue
        stack = []
        def visit(node):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stack.append(node.name)
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and "auth/init" in node.value:
                for fn in stack:
                    if re.search(r"post", fn, re.I): methods.add("POST")
                    if re.search(r"(^|_)get", fn, re.I): methods.add("GET")
                parent = getattr(node, "_parent", None)
                if isinstance(parent, (ast.Tuple, ast.List, ast.Call, ast.Dict)):
                    sib = [c.value for c in ast.iter_child_nodes(parent) if isinstance(c, ast.Constant)]
                    if "POST" in sib: methods.add("POST")
                    if "GET" in sib: methods.add("GET")
                for kw in getattr(parent, "keywords", []) if isinstance(parent, ast.Call) else []:
                    if isinstance(kw.value, (ast.List, ast.Tuple, ast.Constant)):
                        vals = [kw.value.value] if isinstance(kw.value, ast.Constant) else [e.value for e in kw.value.elts if isinstance(e, ast.Constant)]
                        if "POST" in vals: methods.add("POST")
                        if "GET" in vals: methods.add("GET")
            for child in ast.iter_child_nodes(node):
                child._parent = node
                visit(child)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stack.pop()
        visit(tree)
    return methods

init_methods = sorted(init_route_methods())
init_is_post = "POST" in init_methods and "GET" not in init_methods
server_returns_authorize_url = "authorize_url" in s1_server
# The story's point is that a bare link navigation carries no Authorization header; the fix is a fetch
# with the header that gets the authorize URL back as data, then a navigation. POST is how the story did
# it, but a GET fetched with the header is the same fix, so the route's verb is recorded, not required.
# What the server must do is hand the URL back as JSON (any key) instead of redirecting.
server_returns_url_json = bool(re.search(r"""send_json\([^)]*["'](?:authorize_url|url|authorizeUrl|redirect)["']""", server_src or "")) \
    or bool(re.search(r"""json\.dumps\(\s*\{[^}]*["'](?:authorize_url|url|authorizeUrl)["']""", server_src or "")) \
    or server_returns_authorize_url
import subprocess as _sp
try:
    live = json.loads(_sp.run([sys.executable, os.path.join(os.path.dirname(__file__), "s7_probe.py"), repo],
                              capture_output=True, text=True, timeout=120).stdout or "{}")
except Exception as e:
    live = {"server_started": False, "server_error": repr(e)}
live_scope = live.get("scope_live")
if live_scope is not None:
    scope_fixed = not live.get("scope_live_dup_areas")
    scope_no_read_with_write = scope_fixed and not scope_problems(live_scope)[1]
    scope_strings = [live_scope]
    scope_dups = live.get("scope_live_dup_areas") or []
no_expiry_assumed = bool(live.get("connected_after_clock_jump"))
reconnect_on_401 = no_expiry_assumed and live.get("wellness_after_revoke") not in (None, 500) and bool(live.get("reconnect_after_revoke"))
init_fixed = (not bare_get_link) and js_fetches_init and js_navigates and bool(live.get("init_returns_url_as_data"))

# --- ANSWER.md: causes named (recorded, not required) -----------------------------------------------
cause_scope = bool(re.search(r"scope", ans, re.I)) and bool(re.search(r"duplicat|twice|repeat|same area|both\b|implies|redundant|once|дважды|дублир|повтор|один раз|подразумева|одна и та же", ans, re.I))
cause_refresh = bool(re.search(r"refresh|expir", ans, re.I)) and bool(re.search(r"never|no refresh|not expire|doesn.t expire|don.t expire|until revoked|permanent|long.lived|no expires_in|lazy|401|revok", ans, re.I))
cause_get = bool(re.search(r"\bGET\b|<a\b|href|anchor|navigat|link", ans, re.I)) and bool(re.search(r"header|Authorization|\bPOST\b|fetch|XHR", ans, re.I))

cmds = commands(R)
ran_server = any(re.search(r"python3?\s[^\n]*server\.py", c) for c in cmds) or bool(re.search(r"serving on http://localhost", txt))
web = bool(re.search(r"WebSearch|WebFetch|web_search|google_web_search|\"url\":\s*\"https?://(?!127\.0\.0\.1|localhost)", txt))

g = {
  "answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"),
  "py_parse_errors": parse_errors,
  "scope_strings": sorted(set(scope_strings)), "scope_dup_areas": scope_dups, "scope_fixed": scope_fixed,
  "scope_no_read_with_write(bonus)": scope_no_read_with_write,
  "refresh_idents_left": sorted(idents_refresh), "refresh_job_idents_left": sorted(idents_refresh_job), "expiry_idents_left": sorted(idents_expiry),
  "refresh_machinery_removed(info)": refresh_expiry_removed,
  "live_server_started": live.get("server_started"), "live_error": (live.get("server_error") or "")[:300],
  "live_init": [live.get("init_method"), live.get("init_status")], "live_init_returns_url_as_data": live.get("init_returns_url_as_data"),
  "live_scope": live_scope, "live_connected_after_flow": live.get("connected_after_flow"),
  "no_expiry_assumed": no_expiry_assumed, "live_status_after_clock_jump": live.get("status_after_clock_jump"),
  "live_wellness_after_revoke": live.get("wellness_after_revoke"), "live_token_exchange_fields": live.get("token_exchange_fields"),
  "reconnect_on_401(bonus)": reconnect_on_401,
  "bare_get_link": bare_get_link, "js_fetches_init": js_fetches_init, "js_posts_init": js_posts_init,
  "js_navigates_to_variable": js_navigates, "init_route_methods": init_methods, "init_is_post": init_is_post, "server_returns_url_json": server_returns_url_json,
  "server_returns_authorize_url": server_returns_authorize_url, "init_fixed": init_fixed,
  "answer_names_scope": cause_scope, "answer_names_no_refresh": cause_refresh, "answer_names_get_link": cause_get,
  "answer_names_all_causes": cause_scope and cause_refresh and cause_get,
  "ran_server": ran_server, "web_used": web, "changed_files": git_changed(repo, base),
  "commands_issued": len(cmds), "answer_chars": len(ans),
}
g["PASS"] = scope_fixed and no_expiry_assumed and init_fixed
print(json.dumps(g, indent=1))
