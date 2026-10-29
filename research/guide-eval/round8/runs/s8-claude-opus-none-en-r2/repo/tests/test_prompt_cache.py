"""Offline check of the cache layout: a fake LLM that mimics prefix caching.

The fake splits each request into blocks (tools, then system blocks, then message
blocks), writes a cache entry at every cache_control breakpoint and, like the API,
looks back up to 20 block boundaries before a breakpoint for an earlier entry.
Token counts are approximated as chars/4; only the ratios matter here.
"""
import json
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bot  # noqa: E402


def _blocks(req):
    out = [(json.dumps(req["tools"]), False)]
    out += [(b["text"], "cache_control" in b) for b in req["system"]]
    for m in req["messages"]:
        content = m["content"] if isinstance(m["content"], list) else [{"type": "text", "text": m["content"]}]
        out += [(json.dumps(c), "cache_control" in c) for c in content]
    return out


class FakeLLM:
    def __init__(self, script):
        self.cache = set()
        self.script = list(script)  # per call: None (text reply) or a save_fact string

    def create(self, **req):
        blocks = _blocks(req)
        toks = [len(t) // 4 for t, _ in blocks]
        prefixes = ["\x00".join(t for t, _ in blocks[:i + 1]) for i in range(len(blocks))]
        before, read = set(self.cache), 0
        for i, (_, bp) in enumerate(blocks):
            if not bp:
                continue
            for j in range(i, max(-1, i - 20), -1):
                if prefixes[j] in before:
                    read = max(read, sum(toks[:j + 1]))
                    break
            self.cache.add(prefixes[i])
        last_bp = max([i for i, (_, bp) in enumerate(blocks) if bp], default=-1)
        cached_total = sum(toks[:last_bp + 1])
        usage = types.SimpleNamespace(input_tokens=sum(toks) - cached_total, cache_read_input_tokens=read,
                                      cache_creation_input_tokens=cached_total - read, output_tokens=10)
        step = self.script.pop(0)
        if step is None:
            content = [types.SimpleNamespace(type="text", text="ok", model_dump=lambda: {"type": "text", "text": "ok"})]
            stop = "end_turn"
        else:
            d = {"type": "tool_use", "id": f"t{len(self.script)}", "name": "save_fact", "input": {"fact": step}}
            content = [types.SimpleNamespace(type="tool_use", id=d["id"], name="save_fact", input=d["input"],
                                             model_dump=lambda d=d: d)]
            stop = "tool_use"
        return types.SimpleNamespace(content=content, stop_reason=stop, usage=usage)


class CacheLayoutTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        bot.ATHLETES_FILE = os.path.join(self.tmp, "athletes.json")
        bot.USAGE_LOG = os.path.join(self.tmp, "usage.jsonl")
        bot.save_athlete(bot.Athlete(user_id="1", name="Test", facts=["Owns a Garmin 255"]))

    def usage(self):
        with open(bot.USAGE_LOG) as f:
            return [json.loads(l) for l in f]

    def test_save_fact_keeps_prefix_cached(self):
        llm = FakeLLM([None, "Runs Mon/Wed/Fri", None, None, "Has a smart trainer", None])
        bot.reply("1", "hi", llm)
        bot.reply("1", "I run on Mon/Wed/Fri", llm)   # save_fact, then a second round
        bot.reply("1", "how was that", llm)
        bot.reply("1", "I bought a trainer", llm)    # save_fact again
        u = self.usage()
        static = u[0]["cache_creation_input_tokens"]
        self.assertGreater(static, 500)
        for rec in u[1:]:
            # after the first write nothing re-writes more than one fact's worth of tokens
            self.assertLess(rec["cache_creation_input_tokens"], 30, rec)
            self.assertGreaterEqual(rec["cache_read_input_tokens"], static, rec)

    def test_facts_are_in_the_prompt(self):
        a = bot.load_athlete("1")
        text = "".join(b["text"] for b in bot.build_system(a, bot.dt.date(2026, 4, 18)))
        self.assertIn("- Owns a Garmin 255\n", text)
        self.assertIn("Language: en", text)
        self.assertLessEqual(sum("cache_control" in b for b in bot.build_system(a, bot.dt.date.today())), 2)


if __name__ == "__main__":
    unittest.main()
