"""Offline check of the prompt-cache layout (no API calls).

Simulates Anthropic prefix caching: an entry is written at each cache_control
breakpoint whose prefix is >= MIN_TOKENS; a breakpoint reads the longest cached
prefix ending at it or at one of the ~20 block boundaries before it.
Tokens are estimated as chars/3.5 plus a fixed overhead fitted to logs/usage.jsonl.
Run: python3 -I tests/test_prompt_cache.py
"""
import copy, datetime as dt, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bot

MIN_TOKENS = 1024          # Sonnet 4.5 minimum cacheable prefix
LOOKBACK = 20
TOOL_OVERHEAD = 110        # fixed per-request overhead, fitted to logs/usage.jsonl (user 42 ~1046, 77 ~1024)


def blocks_of(req):
    out = [json.dumps(t, sort_keys=True) for t in req["tools"]]
    out += [b["text"] for b in req["system"]]
    marks = [len(req["tools"]) + i for i, b in enumerate(req["system"]) if "cache_control" in b]
    return out, marks


def tok(s):
    return len(s) / 3.5


class Cache:
    def __init__(self):
        self.entries = set()

    def call(self, req):
        blocks, marks = blocks_of(req)
        prefix_tokens = [TOOL_OVERHEAD]
        for b in blocks:
            prefix_tokens.append(prefix_tokens[-1] + tok(b))
        key = lambda i: tuple(blocks[:i + 1])
        read = 0
        for m in marks:
            for j in range(m, max(-1, m - LOOKBACK - 1), -1):
                if key(j) in self.entries:
                    read = max(read, prefix_tokens[j + 1]); break
        cached_to = max((m for m in marks if prefix_tokens[m + 1] >= MIN_TOKENS), default=None)
        for m in marks:
            if prefix_tokens[m + 1] >= MIN_TOKENS:
                self.entries.add(key(m))
        write = (prefix_tokens[cached_to + 1] - read) if cached_to is not None else 0
        return round(read), round(max(write, 0))


def main():
    today = dt.date(2026, 4, 18)
    a = bot.load_athlete("42")
    tools = bot.select_tools("thanks")
    cache = Cache()
    msgs = [{"role": "user", "content": "x"}]
    r1 = cache.call(bot.build_request(a, msgs, tools, today))
    r2 = cache.call(bot.build_request(a, msgs, tools, today))
    old = copy.deepcopy(bot.build_system(a, today))
    a.facts.append("Has a half marathon booked on 14 June in Porto")
    new = bot.build_system(a, today)
    r3 = cache.call(bot.build_request(a, msgs, tools, today))
    print("first call   read/write:", r1)
    print("repeat call  read/write:", r2)
    print("after save   read/write:", r3)

    strip = lambda bs: [b["text"] for b in bs]
    assert strip(new)[:len(old)] == strip(old), "save_fact must only append blocks"
    assert sum("cache_control" in b for b in new) <= 4
    assert new[0]["text"] == bot.build_system(bot.load_athlete("77"), dt.date(2026, 9, 1))[0]["text"], \
        "instructions block must be byte-identical across users and days"
    assert r2[1] == 0 and r2[0] > 0, "repeat call should be fully cached"
    assert r3[0] >= r2[0] and r3[1] < 60, f"memory write should re-cache only the new fact, got {r3}"
    print("ok")


if __name__ == "__main__":
    main()
