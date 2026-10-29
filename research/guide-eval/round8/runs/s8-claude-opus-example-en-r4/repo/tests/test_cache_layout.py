"""Offline check of the system-prompt layout against Anthropic's prefix-cache rules.

FakeLLM models the cache the way the docs describe it: an entry is written at each
cache_control breakpoint, keyed by the exact prefix (tools, then system blocks); on
lookup each breakpoint also checks up to 20 earlier block boundaries for an entry.
Tokens are approximated as len(json)/4, so the numbers are relative, not billing-exact.

Run: python3 -m unittest discover -s tests
"""
import datetime as dt
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bot  # noqa: E402

LOOKBACK = 20


def _strip(block):
    return {k: v for k, v in block.items() if k != "cache_control"}


class FakeLLM:
    def __init__(self, script):
        self.script = list(script)   # per call: None for a text reply, or (tool_name, input)
        self.cache = set()
        self.usage = []

    def create(self, **kw):
        units = [json.dumps(t, sort_keys=True) for t in kw["tools"]] + [json.dumps(_strip(b), sort_keys=True) for b in kw["system"]]
        n_tools = len(kw["tools"])
        marks = [n_tools + i + 1 for i, b in enumerate(kw["system"]) if "cache_control" in b]
        size = lambda n: sum(len(u) for u in units[:n]) // 4
        key = lambda n: "\x00".join(units[:n])
        hit = 0
        for m in marks:
            for n in range(m, max(m - LOOKBACK, 0) - 1, -1):
                if key(n) in self.cache:
                    hit = max(hit, n)
                    break
        for m in marks:
            self.cache.add(key(m))
        read = size(hit)
        created = size(marks[-1]) - read if marks else 0
        self.usage.append((read, created))
        usage = NS(input_tokens=size(len(units)) - size(marks[-1]) if marks else size(len(units)),
                   cache_creation_input_tokens=created, cache_read_input_tokens=read, output_tokens=1)
        step = self.script.pop(0)
        if step is None:
            return NS(stop_reason="end_turn", usage=usage, content=[NS(type="text", text="ok")])
        name, args = step
        block = NS(type="tool_use", id="t1", name=name, input=args)
        block.model_dump = lambda: {"type": "tool_use", "id": "t1", "name": name, "input": args}
        return NS(stop_reason="tool_use", usage=usage, content=[block])


class CacheLayoutTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        bot.ATHLETES_FILE = os.path.join(self.tmp, "athletes.json")
        bot.USAGE_LOG = os.path.join(self.tmp, "usage.jsonl")
        bot.save_athlete(bot.Athlete(user_id="42", name="Marta", facts=["Runs before work, 06:30, Mon/Wed/Fri"]))

    def test_static_block_is_stable(self):
        a = bot.load_athlete("42")
        s1 = bot.build_system(a, dt.date(2026, 4, 18))
        a.facts.append("Owns a Garmin 255")
        s2 = bot.build_system(a, dt.date(2026, 4, 19))
        self.assertEqual(s1[0], s2[0])
        # old cached prefix (everything before the date) is a block-aligned prefix of the new prompt
        old = [_strip(b) for b in s1[:-1]]
        self.assertEqual(old, [_strip(b) for b in s2[:len(old)]])

    def test_save_fact_recaches_only_the_new_fact(self):
        llm = FakeLLM([None,                                       # msg 1: warm the cache
                       ("save_fact", {"fact": "Has a 10k race booked on 2026-05-10"}), None,   # msg 2
                       None])                                      # msg 3: follow-up
        for text in ("hi", "I booked a 10k", "thanks"):
            bot.reply("42", text, llm=llm)
        full = llm.usage[0][1]
        _, (r_save, c_save), (r_after, c_after), (r_next, c_next) = llm.usage
        self.assertEqual(c_save, 0)
        self.assertLess(c_after, 0.05 * full, llm.usage)          # round after save_fact: just the fact
        self.assertGreater(r_after, 0.95 * full, llm.usage)
        self.assertEqual(c_next, 0)

    def test_new_day_busts_nothing(self):
        a = bot.load_athlete("42")
        llm = FakeLLM([None, None])
        for day in (dt.date(2026, 4, 18), dt.date(2026, 4, 19)):
            llm.create(**bot.build_request(a, [{"role": "user", "content": "hi"}], bot.select_tools("hi"), day))
        self.assertEqual(llm.usage[1][1], 0)


if __name__ == "__main__":
    unittest.main()
