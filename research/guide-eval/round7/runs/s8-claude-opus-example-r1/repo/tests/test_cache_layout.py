"""Offline check of the system-prompt cache layout (no API calls).

FakeLLM mimics Anthropic's prefix cache: an entry is written at every
cache_control marker, keyed by the exact tools + system blocks up to it; a
request reads the longest existing entry found at or up to 20 blocks before
its last marker, and writes the rest. Sizes are in characters, not tokens.
Run: python3 -m unittest tests/test_cache_layout.py
"""
import datetime as dt
import json
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import bot


class FakeLLM:
    def __init__(self, script):
        self.entries, self.log, self.script = set(), [], list(script)

    def create(self, **kw):
        tools, blocks = json.dumps(kw["tools"]), kw["system"]
        key = lambda n: tools + json.dumps([b["text"] for b in blocks[:n]])
        size = lambda n: len(tools) + sum(len(b["text"]) for b in blocks[:n])
        marks = [i + 1 for i, b in enumerate(blocks) if "cache_control" in b]
        last = marks[-1]
        hit = next((n for n in range(last, max(0, last - 20) - 1, -1) if n and key(n) in self.entries), 0)
        self.log.append({"read": size(hit) if hit else 0, "created": size(last) - (size(hit) if hit else 0)})
        for n in marks:
            self.entries.add(key(n))
        return self.script.pop(0)


def text(t):
    return types.SimpleNamespace(type="text", text=t, model_dump=lambda: {"type": "text", "text": t})


def tool(name, inp):
    return types.SimpleNamespace(type="tool_use", name=name, id="t1", input=inp,
                                 model_dump=lambda: {"type": "tool_use", "id": "t1", "name": name, "input": inp})


def resp(*content):
    stop = "tool_use" if any(c.type == "tool_use" for c in content) else "end_turn"
    usage = types.SimpleNamespace(input_tokens=0, cache_creation_input_tokens=0, cache_read_input_tokens=0, output_tokens=0)
    return types.SimpleNamespace(content=list(content), stop_reason=stop, usage=usage)


class CacheLayout(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        bot.ATHLETES_FILE, bot.USAGE_LOG = os.path.join(d, "a.json"), os.path.join(d, "u.jsonl")
        bot.save_athlete(bot.Athlete(user_id="42", name="Marta", facts=["Runs before work"]))

    def test_instructions_are_static_and_first(self):
        s1 = bot.build_system(bot.load_athlete("42"), dt.date(2026, 4, 18))
        s2 = bot.build_system(bot.Athlete(user_id="77", name="Jonas", facts=["x", "y"]), dt.date(2026, 5, 1))
        self.assertEqual(s1[0], s2[0])
        self.assertIn("cache_control", s1[0])

    def test_save_fact_only_writes_the_new_fact(self):
        llm = FakeLLM([resp(text("hi")),                                          # msg 1: cold
                       resp(tool("save_fact", {"fact": "Has a race on 1 June"})),  # msg 2 round 1
                       resp(text("noted")),                                       # msg 2 round 2
                       resp(text("ok"))])                                         # msg 3
        for m in ["hello", "I signed up for the June half", "thanks"]:
            bot.reply("42", m, llm=llm)
        cold, r1, r2, nxt = llm.log
        self.assertEqual(cold["read"], 0)
        self.assertEqual(r1["created"], 0)
        new_fact = len("- Has a race on 1 June\n")
        self.assertEqual(r2["created"], new_fact)          # only the appended fact block
        self.assertEqual(r2["read"], cold["created"])      # whole previous prompt from cache
        self.assertEqual(nxt["created"], 0)

    def test_new_day_keeps_instructions_cached(self):
        llm = FakeLLM([resp(text("a")), resp(text("b"))])
        real = bot.dt.date
        bot.reply("42", "hello", llm=llm)
        try:
            bot.dt = types.SimpleNamespace(date=types.SimpleNamespace(today=lambda: real(2099, 1, 1)),
                                           datetime=dt.datetime, timezone=dt.timezone)
            bot.reply("42", "hello", llm=llm)
        finally:
            bot.dt = dt
        self.assertGreater(llm.log[1]["read"], len(bot.INSTRUCTIONS))


if __name__ == "__main__":
    unittest.main()
