"""s8: one cache_control marker on a single system block, so every save_fact evicts the whole prefix.
Hidden answer key (Anthropic prompt-caching docs allow up to 4 breakpoints):
  system becomes a list of >= 2 text blocks; the static instructions block comes first, is byte-identical
  across users/days/facts and carries cache_control; the per-user tail (date, profile, zones, goal, facts,
  language) is a separate block after it. A memory write then re-caches only the tail.
PASS = >= 2 blocks AND a memory write keeps the instructions cached AND total cache_control markers
       (system + tools) <= 4. "Keeps the instructions cached" is simulated with the documented cache rules:
       the request before the write creates an entry at each cache_control block (the prefix up to it); the
       request after the write (same athlete, same date, one more fact) looks back up to 20 block boundaries
       from each of its markers for an entry it can read; PASS needs the longest such hit to hold the
       instructions. This accepts the story's design (static block first, marker on it, tail after), a
       per-athlete cached prefix (instructions + profile, facts after), and a marker on the last of
       append-only fact blocks (the lookback finds the previous entry); it rejects one block whose text
       changes, and a marker placed before the instructions.
       The story's own design, a prefix byte-identical across athletes, is recorded as
       shared_prefix_across_athletes (information only).
Extra (recorded, not required): tail block marked; tools / tool filtering changed; ANSWER mentions
       prefix/breakpoint; changed files; command count; answer length.
How: bot.py is imported in a subprocess with the `anthropic` SDK stubbed (a recording client), and the
system prompt is built for two athletes via build_system / build_request / reply, whichever exists.
If none works, source-level signals are recorded and PASS is false with reason "probe_failed".
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R)
txt = run_text(R)
src = read(os.path.join(repo, "bot.py"))
changed = git_changed(repo, base)  # before the probe imports anything

PROBE = r'''
import sys, os, json, types, inspect, datetime as dt, dataclasses, importlib.abc, importlib.util, tempfile
sys.dont_write_bytecode = True
repo = sys.argv[1]
calls = []
class Dummy:
    def __init__(self, *a, **k): pass
    def __call__(self, *a, **k): return Dummy()
    def __getattr__(self, n): return Dummy()
class _Resp:
    stop_reason = "end_turn"; content = [types.SimpleNamespace(type="text", text="ok")]
    usage = types.SimpleNamespace(input_tokens=1, cache_creation_input_tokens=0, cache_read_input_tokens=0, output_tokens=1)
class _Messages:
    def create(self, *a, **kw): calls.append(kw); return _Resp()
class Anthropic:
    def __init__(self, *a, **k): self.messages = _Messages(); self.beta = types.SimpleNamespace(messages=_Messages())
class Finder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, name, path, target=None):
        if name == "anthropic" or name.startswith("anthropic."):
            return importlib.util.spec_from_loader(name, self, is_package=True)
    def create_module(self, spec):
        m = types.ModuleType(spec.name); m.__path__ = []; m.Anthropic = Anthropic; m.AsyncAnthropic = Anthropic
        m.__getattr__ = lambda n: Dummy
        return m
    def exec_module(self, m): pass
sys.meta_path.insert(0, Finder())
os.environ.setdefault("COACH_ANTHROPIC_KEY", "sk-ant-test")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.chdir(repo); sys.path.insert(0, repo)
spec = importlib.util.spec_from_file_location("bot", os.path.join(repo, "bot.py"))
bot = importlib.util.module_from_spec(spec); sys.modules["bot"] = bot; spec.loader.exec_module(bot)

POOL = {
 "A": dict(user_id="9001", name="Ines", lang="es", sport="running", goal="10 km under 50 min in May",
           zones={"Z1": "<140", "Z2": "140-154", "Z3": "154-165", "Z4": "165-175", "Z5": ">175"},
           facts=["Trains on a treadmill in winter", "Had a stress fracture in 2023"]),
 "B": dict(user_id="9002", name="Olaf", lang="de", sport="cycling", goal="finish a 200 km brevet",
           zones={"Z1": "<128", "Z2": "128-144", "Z3": "144-156", "Z4": "156-166", "Z5": ">166"},
           facts=["Commutes 20 km by bike", "Owns a power meter", "Races on Sundays", "Vegetarian"]),
}
POOL["A2"] = dict(POOL["A"], facts=POOL["A"]["facts"] + ["Prefers morning sessions"])
DATES = {"A": dt.date(2026, 4, 21), "A2": dt.date(2026, 4, 21), "B": dt.date(2026, 5, 3)}

def make_athlete(key):
    pool = POOL[key]
    A = getattr(bot, "Athlete", None)
    if A is None: return dict(pool)
    if dataclasses.is_dataclass(A):
        names = [f.name for f in dataclasses.fields(A)]
    else:
        names = list(inspect.signature(A).parameters)
    kw = {n: pool[n] for n in names if n in pool}
    for n in names:
        if n not in kw:
            try: kw[n] = "x"
            except Exception: pass
    try: return A(**kw)
    except TypeError: return A(**{n: pool[n] for n in names if n in pool})

def fill(fn, key, ath, tools):
    kw = {}
    for p in inspect.signature(fn).parameters.values():
        n = p.name.lower()
        if n in ("a", "athlete", "profile", "user", "record", "ath"): kw[p.name] = ath
        elif n in ("today", "date", "day", "now"): kw[p.name] = DATES[key]
        elif n in ("messages", "msgs", "history"): kw[p.name] = [{"role": "user", "content": "hi"}]
        elif n in ("tools", "tool_list"): kw[p.name] = tools
        elif n in ("text", "message", "msg", "query", "user_text"): kw[p.name] = "hi"
        elif n in ("user_id", "uid", "chat_id"): kw[p.name] = POOL[key]["user_id"]
        elif n in ("facts", "memory"): kw[p.name] = POOL[key]["facts"]
        elif p.default is inspect._empty and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD): kw[p.name] = None
    return fn(**kw)

def norm(sysv):
    if sysv is None: return None
    if isinstance(sysv, str): return [{"type": "text", "text": sysv}]
    out = []
    for b in sysv:
        if isinstance(b, dict): out.append({"type": b.get("type"), "text": b.get("text", ""), "cache_control": b.get("cache_control")})
        else: out.append({"type": getattr(b, "type", None), "text": getattr(b, "text", ""), "cache_control": getattr(b, "cache_control", None)})
    return out

def tools_for(ath, key):
    for name in ("select_tools", "pick_tools", "tools_for"):
        fn = getattr(bot, name, None)
        if fn:
            try: return fill(fn, key, ath, [])
            except Exception: pass
    for name in ("CORE_TOOLS", "TOOLS", "ALL_TOOLS"):
        v = getattr(bot, name, None)
        if isinstance(v, list): return v
    return []

res = {"method": None, "errors": []}
for key in ("A", "A2", "B"):
    ath = make_athlete(key); tools = tools_for(ath, key); got = None; method = None
    for name in ("build_request", "build_system", "system_prompt", "build_prompt", "make_system", "system_blocks"):
        fn = getattr(bot, name, None)
        if not callable(fn): continue
        try:
            v = fill(fn, key, ath, tools)
            if isinstance(v, dict) and "system" in v:
                got = v["system"]; tools = v.get("tools", tools); method = name; break
            if isinstance(v, (str, list)):
                got = v; method = name; break
        except Exception as e:
            res["errors"].append(f"{name}: {type(e).__name__}: {e}")
    if got is None and hasattr(bot, "reply"):
        try:
            tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); tmp.write("{}"); tmp.close()
            if hasattr(bot, "ATHLETES_FILE"): bot.ATHLETES_FILE = tmp.name
            if hasattr(bot, "save_athlete"): bot.save_athlete(ath)
            calls.clear()
            kw = {"user_id": POOL[key]["user_id"], "text": "hi"}
            sig = inspect.signature(bot.reply)
            if "llm" in sig.parameters:
                class _L:
                    def create(self, **k): calls.append(k); return _Resp()
                kw["llm"] = _L()
            bot.reply(**{k: v for k, v in kw.items() if k in sig.parameters})
            if calls:
                got = calls[0].get("system"); tools = calls[0].get("tools", tools); method = "reply"
        except Exception as e:
            res["errors"].append(f"reply: {type(e).__name__}: {e}")
    res["sys" + key] = norm(got); res["tools" + key] = tools if isinstance(tools, list) else []
    res["method"] = method or res["method"]
print(json.dumps(res, default=str))
'''

def probe():
    """Run the probe against a scratch copy of the repo so importing / calling reply() cannot touch the run dir."""
    import shutil, tempfile
    try:
        tmp = tempfile.mkdtemp(prefix="s8probe-")
        copy = os.path.join(tmp, "repo")
        shutil.copytree(repo, copy, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        p = subprocess.run([sys.executable, "-I", "-B", "-c", PROBE, copy], capture_output=True, text=True, timeout=30)
        shutil.rmtree(tmp, ignore_errors=True)
        for line in reversed(p.stdout.splitlines()):
            if line.startswith("{"):
                return json.loads(line), (p.stderr[-800:] if p.returncode else "")
        return None, (p.stderr[-800:] or p.stdout[-800:])
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

def count_markers(blocks):
    return sum(1 for b in (blocks or []) if isinstance(b, dict) and b.get("cache_control"))

pr, perr = probe()
sysA = sysB = None; method = None
if pr:
    sysA, sysB, method = pr.get("sysA"), pr.get("sysB"), pr.get("method")

n_blocks = len(sysA) if sysA else 0
static_prefix = 0; static_text = ""; tail_text = ""
if sysA and sysB:
    for a, b in zip(sysA, sysB):
        if a["text"] == b["text"] and a["type"] == b["type"]:
            static_prefix += 1; static_text += a["text"]
        else:
            break
    tail_text = "".join(b["text"] for b in sysA[static_prefix:])
static_holds_instructions = len(static_text) >= 400 and "coach" in static_text.lower()
static_marked = static_prefix >= 1 and bool(sysA[static_prefix - 1].get("cache_control"))
tail_exists = n_blocks > static_prefix
tail_marked = tail_exists and bool(sysA[-1].get("cache_control"))
markers_system = count_markers(sysA)
markers_tools = count_markers(pr.get("toolsA") if pr else [])
# messages markers are per-call; the tool loop in this fixture has none
markers_total = markers_system + markers_tools
first_block_differs = bool(sysA and sysB and n_blocks >= 1 and sysA[0]["text"] != sysB[0]["text"])

# the memory-write simulation: sysA is the request before save_fact, sysA2 the one after (same athlete, same date)
sysA2 = pr.get("sysA2") if pr else None
def cache_hit_after_write(old, new):
    if not old or not new: return ""
    entries = {"".join(b["text"] for b in old[:i + 1]) for i, b in enumerate(old) if b.get("cache_control")}
    best = ""
    for j, b in enumerate(new):
        if not b.get("cache_control"): continue
        for k in range(0, 21):
            i = j - k
            if i < 0: break
            pre = "".join(x["text"] for x in new[:i + 1])
            if pre in entries and len(pre) > len(best): best = pre
    return best
hit = cache_hit_after_write(sysA, sysA2)
write_keeps_instructions = len(hit) >= 400 and "coach" in hit.lower()
same_date_same_facts_identical = bool(sysA and sysA2) and "".join(b["text"] for b in sysA) != "".join(b["text"] for b in sysA2)

# source-level signals (always recorded; the only evidence when the probe fails)
src_nc = re.sub(r"#.*", "", src)
markers_in_source = len(re.findall(r"cache_control", src_nc))
base_src = subprocess.run(["git", "show", f"{base}:bot.py"], cwd=repo, capture_output=True, text=True).stdout
def tools_region(s):
    i = s.find("CORE_TOOLS"); j = s.find("def run_tool")
    return s[i:j] if i != -1 and j != -1 else s
tools_changed = tools_region(base_src).strip() != tools_region(src).strip()
tools_marker_in_source = "cache_control" in tools_region(src_nc)

answer_prefix = bool(re.search(r"prefix|breakpoint|break-point|break point|cache point|segment|two (cache_control |cache |content )?blocks|4 (cache_control )?markers|four (cache_control )?markers|up to 4", ans, re.I))
answer_two_blocks = bool(re.search(r"two (text |content |system |separate |cache_control |cache )?blocks|second block|static (instructions? )?block|split the system", ans, re.I))
cmds = commands(R)
ran_bot = any(re.search(r"python3?\s+(-c\s+.*import bot|bot\.py)|import bot", c) for c in cmds)
web = bool(re.search(r"WebSearch|WebFetch|web_search|google_web_search|docs\.(claude|anthropic)\.com", txt))

g = {
  "answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"),
  "probe_method": method, "probe_error": (perr or (pr or {}).get("errors") or None) if not sysA else None,
  "n_blocks": n_blocks, "static_prefix_blocks": static_prefix, "static_chars": len(static_text), "tail_chars": len(tail_text),
  "memory_write_keeps_instructions_cached": write_keeps_instructions, "cache_hit_chars_after_write": len(hit),
  "probe_saw_the_new_fact": same_date_same_facts_identical,
  "shared_prefix_across_athletes(info)": bool(static_prefix >= 1 and static_holds_instructions and static_marked),
  "static_holds_instructions": static_holds_instructions, "static_marked": static_marked,
  "static_independent_of_facts_and_date": static_prefix >= 1, "first_block_differs_between_users": first_block_differs,
  "tail_after_static": tail_exists, "tail_marked": tail_marked,
  "markers_system": markers_system, "markers_tools": markers_tools, "markers_total": markers_total, "markers_in_source": markers_in_source,
  "tools_changed": tools_changed, "tools_marker_in_source": tools_marker_in_source,
  "answer_mentions_prefix_or_breakpoint": answer_prefix, "answer_mentions_two_blocks": answer_two_blocks,
  "ran_bot": ran_bot, "web_used": web, "changed_files": changed, "commands_issued": len(cmds), "answer_chars": len(ans),
}
if sysA is None:
    g["fail_reason"] = "probe_failed"
    g["PASS"] = False
else:
    g["PASS"] = bool(n_blocks >= 2 and write_keeps_instructions and markers_total <= 4)
    if not g["PASS"]:
        g["fail_reason"] = ("one_block" if n_blocks < 2 else "tail_first_or_static_interpolated" if static_prefix == 0
                            else "static_not_marked" if not static_marked else "no_tail_block" if not tail_exists
                            else "too_many_markers" if markers_total > 4 else "static_block_too_small")
print(json.dumps(g, indent=1))
