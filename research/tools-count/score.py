#!/usr/bin/env python3
"""Score one run directory. usage: score.py <run_dir>  -> prints a JSON row.

Ground truth for what the model did = calls.jsonl written by the fake MCP server (never the model's own claims).
Token/time/cost numbers come from each CLI's structured output.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from server import READONLY, POOL  # noqa: E402

R = sys.argv[1]
meta = json.load(open(os.path.join(R, "meta.json")))
tasks = {t["id"]: t for t in json.load(open(os.path.join(HERE, "tasks.json")))["tasks"]}
task = tasks[meta["task"]]
M = meta["model"]

def jl(path):
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path, errors="replace"):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out

# ---------------- what the model called (server log) ----------------
log = jl(os.path.join(R, "calls.jsonl"))
start = next((e for e in log if e.get("event") == "start"), {})
calls = [e for e in log if e.get("event") == "call"]

def norm(x):
    return os.path.basename(str(x).strip().lstrip("./")).lower()

def check(c, args, matched):
    v = args.get(c["arg"]); op = c["op"]; want = c["value"]
    if op == "eq":
        if isinstance(want, str):
            return v is not None and norm(v) == norm(want)
        return v == want or (isinstance(v, str) and v.strip() == str(want))
    if op == "seq":
        return isinstance(v, list) and [norm(x) for x in v] == [norm(x) for x in want]
    if op == "in":
        return isinstance(v, str) and v.lower() in [w.lower() for w in want]
    if op == "contains":
        return isinstance(v, str) and want.lower() in v.lower()
    if op == "pageset":
        def parse(x):
            if isinstance(x, list): return {int(i) for i in x}
            if isinstance(x, int): return {x}
            out = set()
            for part in str(x).replace(" ", "").split(","):
                if not part: continue
                if "-" in part:
                    lo, hi = part.split("-", 1); out |= set(range(int(lo), int(hi) + 1))
                else: out.add(int(part))
            return out
        try: return v is not None and parse(v) == set(want)
        except Exception: return False
    if op == "from_step":
        prev = matched[want] if want < len(matched) else None
        out = (prev or {}).get("result", {}) or {}
        return prev is not None and v is not None and norm(v) == norm(out.get("output", "\0"))
    raise ValueError(op)

expected = task["expected"]
exp_tools = [s["tool"] for s in expected]
ok_calls = [c for c in calls if not c.get("error")]

# tools_ok: expected tools appear, in order, among successful calls
def subseq(seq, want):
    i = 0
    for x in seq:
        if i < len(want) and x == want[i]:
            i += 1
    return i == len(want)
tools_ok = subseq([c["op"] for c in ok_calls], exp_tools)

# args_ok: in-order matching where every step's key-arg checks pass
def match_with_args():
    matched = []; j = 0
    for step in expected:
        hit = None
        while j < len(ok_calls):
            c = ok_calls[j]; j += 1
            if c["op"] == step["tool"] and all(check(ch, c.get("args") or {}, matched) for ch in step["checks"]):
                hit = c; break
        if hit is None:
            return False, matched
        matched.append(hit)
    return True, matched
args_ok, _ = match_with_args()
args_ok = bool(tools_ok and args_ok)

# wrong = a wrong mutating operation that actually executed; failed attempts (server error, nothing done) are counted apart
wrong = [c for c in ok_calls if c.get("op") not in exp_tools and c.get("op") not in READONLY]
wrong_attempts = [c for c in calls if c.get("error") and c.get("op") not in exp_tools and c.get("op") not in READONLY]
extra_ro = [c for c in calls if c.get("op") not in exp_tools and c.get("op") in READONLY]
repeats = max(0, sum(1 for c in ok_calls if c["op"] in exp_tools) - len(exp_tools))
err_calls = [c for c in calls if c.get("error")]
neighbors_present = [n for n in task.get("neighbors", []) if n in (start.get("tools") or [])] if meta["variant"] != "GROUPED" else ["(grouped)"]

# ---------------- harness output: tokens, time, cost, built-ins, errors ----------------
agent = jl(os.path.join(R, "agent.log"))
err_txt = open(os.path.join(R, "agent.err"), errors="replace").read() if os.path.exists(os.path.join(R, "agent.err")) else ""
u = {"model_id": None, "input_tokens_total": None, "input_uncached": None, "cache_read": None, "cache_write": None,
     "output_tokens": None, "reasoning_tokens": None, "first_call_input": None, "model_calls": None,
     "cost_usd": None, "cli_duration_s": None, "builtin_calls": 0, "builtin_names": [], "harness_error": "", "final_text": ""}
ALLOWED = set()
if M == "claude":
    seen = {}
    for o in agent:
        if o.get("type") == "system" and o.get("subtype") == "init":
            u["model_id"] = o.get("model")
            u["available_builtins"] = [t for t in o.get("tools", []) if not t.startswith("mcp__")]
            u["available_mcp_tools"] = len([t for t in o.get("tools", []) if t.startswith("mcp__")])
        elif o.get("type") == "assistant":
            m = o.get("message", {})
            if m.get("id") and m["id"] not in seen and m.get("usage"):
                us = m["usage"]
                seen[m["id"]] = (us.get("input_tokens") or 0) + (us.get("cache_creation_input_tokens") or 0) + (us.get("cache_read_input_tokens") or 0)
            for c in m.get("content", []):
                if c.get("type") == "tool_use" and not c["name"].startswith("mcp__"):
                    u["builtin_calls"] += 1; u["builtin_names"].append(c["name"])
        elif o.get("type") == "result":
            us = o.get("usage", {})
            u["input_uncached"] = us.get("input_tokens"); u["cache_read"] = us.get("cache_read_input_tokens"); u["cache_write"] = us.get("cache_creation_input_tokens")
            u["input_tokens_total"] = sum(x or 0 for x in (u["input_uncached"], u["cache_read"], u["cache_write"]))
            u["output_tokens"] = us.get("output_tokens"); u["reasoning_tokens"] = (us.get("output_tokens_details") or {}).get("thinking_tokens")
            u["cost_usd"] = o.get("total_cost_usd"); u["cli_duration_s"] = (o.get("duration_ms") or 0) / 1000
            u["final_text"] = (o.get("result") or "")[:500]
            if o.get("is_error"):
                u["harness_error"] = (o.get("result") or o.get("subtype") or "error")[:300]
    if seen:
        u["first_call_input"] = list(seen.values())[0]; u["model_calls"] = len(seen)
elif M == "codex":
    for o in agent:
        t = o.get("type")
        if t == "turn.completed":
            us = o.get("usage", {})
            u["input_tokens_total"] = us.get("input_tokens"); u["cache_read"] = us.get("cached_input_tokens")
            u["input_uncached"] = (us.get("input_tokens") or 0) - (us.get("cached_input_tokens") or 0)
            u["output_tokens"] = us.get("output_tokens"); u["reasoning_tokens"] = us.get("reasoning_output_tokens")
        elif t in ("turn.failed", "error"):
            msg = json.dumps(o)[:300]
            u["harness_error"] = (u["harness_error"] + " " + msg).strip()[:600]
        elif t == "item.completed":
            it = o.get("item", {})
            if it.get("type") == "agent_message":
                u["final_text"] = (it.get("text") or "")[:500]
            elif it.get("type") == "error":
                if "unrecognized configuration" not in (it.get("message") or ""):
                    u["harness_error"] = (u["harness_error"] + " " + (it.get("message") or ""))[:600]
            elif it.get("type") not in ("mcp_tool_call", "reasoning", "todo_list"):
                u["builtin_calls"] += 1; u["builtin_names"].append(it.get("type"))
    roll = jl(os.path.join(R, "rollout.jsonl"))
    lasts = []
    for o in roll:
        p = o.get("payload", {})
        if o.get("type") == "turn_context" and not u["model_id"]:
            u["model_id"] = p.get("model"); u["reasoning_effort"] = (p.get("collaboration_mode") or {}).get("settings", {}).get("reasoning_effort")
        if p.get("type") == "token_count" and p.get("info"):
            lu = p["info"].get("last_token_usage") or {}
            key = json.dumps(p["info"].get("total_token_usage"))
            if not lasts or lasts[-1][0] != key:
                lasts.append((key, lu.get("input_tokens")))
        if p.get("type") in ("custom_tool_call", "function_call"):
            nm = p.get("name")
            if nm not in ("exec", "wait"):
                u["builtin_calls"] += 1; u["builtin_names"].append(nm)
            u.setdefault("exec_calls", 0)
            u["exec_calls"] += 1
    if lasts:
        u["first_call_input"] = lasts[0][1]; u["model_calls"] = len(lasts)
elif M == "gemini":
    first = None; n_steps = 0
    for o in agent:
        su = o.get("step_update")
        if su and su.get("state") == "DONE":
            if su.get("usage"):
                n_steps += 1
                if first is None:
                    us = su["usage"]; first = (us.get("input_tokens") or 0) + (us.get("cache_read_tokens") or 0)
            if su.get("step_type") == "tool":
                nm = su.get("tool_name")
                params = (su.get("tool_info") or {}).get("parameters") or {}
                if nm == "call_mcp_tool":
                    pass
                elif nm == "view_file" and "/antigravity-cli/mcp/" in str(params.get("AbsolutePath", "")):
                    u.setdefault("schema_reads", 0); u["schema_reads"] += 1
                else:
                    u["builtin_calls"] += 1; u["builtin_names"].append(f"{nm}:{json.dumps(params)[:120]}")
        if o.get("event") == "result":
            r = o["result"]; us = r.get("usage", {})
            u["input_uncached"] = us.get("input_tokens"); u["cache_read"] = us.get("cache_read_tokens")
            u["input_tokens_total"] = (us.get("input_tokens") or 0) + (us.get("cache_read_tokens") or 0)
            u["output_tokens"] = us.get("output_tokens"); u["reasoning_tokens"] = us.get("thinking_tokens")
            u["final_text"] = (r.get("response") or "")[:500]
            if r.get("status") not in (None, "SUCCESS"):
                u["harness_error"] = f"status={r.get('status')}"
    u["model_id"] = "gemini-3.1-pro-high (agy --model)"
    u["first_call_input"] = first; u["model_calls"] = n_steps or None
    m = re.search(r"AGY_ERROR: (.*)", err_txt)
    if m:
        u["harness_error"] = (u["harness_error"] + " " + m.group(1))[:600]

RL = re.compile(r"rate.?limit|usage limit|quota|resource.?exhausted|\b429\b|credits balance|hit your limit|limit reached|too many requests|overloaded|\b529\b", re.I)
err_blob = u["harness_error"] + " " + "\n".join(l for l in err_txt.splitlines() if re.search(r"error|limit|quota", l, re.I))[:2000]
if meta.get("timeout"):
    status = "timeout"
elif RL.search(err_blob):
    status = "ratelimited"
elif meta["exit_code"] != 0 or u["harness_error"]:
    status = "error"
elif u["input_tokens_total"] is None:
    status = "error"
else:
    status = "ok"

success = bool(tools_ok and args_ok and not wrong)
row = {
    "phase": meta["phase"], "model": M, "variant": meta["variant"], "n_tools": len(start.get("tools") or []) or None,
    "task": meta["task"], "kind": task["kind"], "rep": meta["rep"], "status": status,
    "success": success, "tools_ok": tools_ok, "args_ok": args_ok, "strict": bool(success and not extra_ro and repeats == 0),
    "n_calls": len(calls), "n_expected": len(expected), "wrong_calls": len(wrong), "wrong_ops": [c.get("op") for c in wrong], "failed_wrong_attempts": len(wrong_attempts),
    "extra_readonly": len(extra_ro), "repeat_calls": repeats, "error_calls": len(err_calls),
    "called_ops": [c.get("op") for c in calls], "called_tools": [c.get("tool") for c in calls],
    "neighbors_present": neighbors_present,
    "wall_s": meta["wall_s"], "exit_code": meta["exit_code"],
}
row.update(u)
print(json.dumps(row, ensure_ascii=False))
