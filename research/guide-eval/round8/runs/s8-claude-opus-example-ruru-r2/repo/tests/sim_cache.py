"""Offline check of the prompt layout against a fake prefix cache (no API calls).

Run: python3 tests/sim_cache.py          (current layout)
     python3 tests/sim_cache.py --naive  (two cache_control markers, for comparison)
The fake cache mimics Anthropic's rules that matter here: a breakpoint caches the
whole prefix (tools, then system blocks) up to it, only if that prefix is at least
MIN_CACHE_TOKENS; a hit needs the prefix to be identical byte for byte. Token
counts are a chars/3.6 estimate plus a tool-use overhead, calibrated so the
default prompt lands near the ~1024-1046 tokens seen in logs/usage.jsonl.
"""
import json, os, shutil, sys, tempfile, types
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bot

MIN_CACHE_TOKENS = 1024          # Sonnet 4.5
tok = lambda s: round(len(s) / 3.6)
TOOL_OVERHEAD = 150


class FakeLLM:
    def __init__(self, script):
        self.cache, self.script = set(), list(script)   # script: tool name to call in round 1, or None

    def create(self, **kw):
        parts = [(json.dumps(kw["tools"], sort_keys=True), TOOL_OVERHEAD + tok(json.dumps(kw["tools"])), False)]
        parts += [(b["text"], tok(b["text"]), "cache_control" in b) for b in kw["system"]]
        prefix, n, best_read, created, breakpoints = "", 0, 0, 0, []
        for text, t, bp in parts:
            prefix += "\x00" + text; n += t
            if bp:
                breakpoints.append((prefix, n))
        for p, n_p in breakpoints:
            if p in self.cache:
                best_read = n_p
        for p, n_p in breakpoints:
            if n_p >= MIN_CACHE_TOKENS and p not in self.cache:
                self.cache.add(p)
        last = max([n_p for p, n_p in breakpoints if n_p >= MIN_CACHE_TOKENS], default=0)
        created = max(0, last - best_read)
        total = n + 30 * len(kw["messages"])
        usage = types.SimpleNamespace(input_tokens=total - best_read - created, cache_creation_input_tokens=created,
                                      cache_read_input_tokens=best_read, output_tokens=50)
        first_round = len(kw["messages"]) == 1
        tool = self.script.pop(0) if first_round else None
        if tool:
            arg = {"save_fact": {"fact": f"Fact number {len(self.cache)} about the athlete's week"},
                   "log_session": {"minutes": 40}}[tool]
            block = types.SimpleNamespace(type="tool_use", name=tool, id="t1", input=arg,
                                          model_dump=lambda: {"type": "tool_use", "id": "t1", "name": tool, "input": arg})
            return types.SimpleNamespace(content=[block], stop_reason="tool_use", usage=usage)
        text = types.SimpleNamespace(type="text", text="ok", model_dump=lambda: {"type": "text", "text": "ok"})
        return types.SimpleNamespace(content=[text], stop_reason="end_turn", usage=usage)


def naive_two_markers(a, today, n_cached):
    """The obvious fix: marker after INSTRUCTIONS, marker after the athlete context."""
    return [{"type": "text", "text": bot.INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": bot.athlete_profile(a, a.facts) + "\n" + bot.volatile_tail(today, []),
             "cache_control": {"type": "ephemeral"}}]


def main():
    if "--naive" in sys.argv:
        bot.build_system = naive_two_markers
    tmp = tempfile.mkdtemp()
    bot.ATHLETES_FILE = os.path.join(tmp, "athletes.json")
    bot.USAGE_LOG = os.path.join(tmp, "usage.jsonl")
    shutil.copy(os.path.join(os.path.dirname(__file__), "..", "data", "athletes.json"), bot.ATHLETES_FILE)
    script = [None, None, "save_fact", None, "log_session", "save_fact", None, None]
    llm = FakeLLM(script)
    for _ in range(len(script)):
        bot.reply("42", "hello", llm=llm)
    rows = [json.loads(l) for l in open(bot.USAGE_LOG)]
    for r in rows:
        print(f"round {r['round']} tool={r.get('tool') or '-':12} create={r['cache_creation_input_tokens']:5} "
              f"read={r['cache_read_input_tokens']:5} uncached={r['input_tokens']:4}")
    creates = [r["cache_creation_input_tokens"] for r in rows]
    print("total cache_creation:", sum(creates), " total cache_read:", sum(r["cache_read_input_tokens"] for r in rows))
    if "--naive" in sys.argv:
        return
    assert creates[0] > 0 and sum(creates[1:]) == 0, "only the first call may create the cache"
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
