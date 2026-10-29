"""Offline check of the system-prompt cache layout (no API calls).

Simulates Anthropic prompt caching closely enough to catch layout regressions:
prefix match at content-block boundaries, writes only at explicit breakpoints whose
prefix is >= MIN_CACHEABLE tokens, lookback of up to 20 blocks before a breakpoint.
Token counts are a rough estimate (chars / 3.2), calibrated against logs/usage.jsonl.
Run: python3 -m unittest discover tests
"""
import copy
import datetime as dt
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bot  # noqa: E402

MIN_CACHEABLE = 1024
TOOL_OVERHEAD = 35  # tuned so the first call for user 77 lands near the 1024 seen in logs/usage.jsonl


def ntok(text):
    return max(1, round(len(text) / 3.2))


def flatten(system, tools):
    """Prefix as (key, tokens, has_marker) per block: tools first, then system blocks."""
    out = [("tools:" + json.dumps(tools, sort_keys=True), ntok(json.dumps(tools)) + TOOL_OVERHEAD, False)]
    out += [(b["text"], ntok(b["text"]), "cache_control" in b) for b in system]
    return out


class Cache:
    def __init__(self):
        self.entries = set()

    def call(self, system, tools):
        blocks = flatten(system, tools)
        keys = [tuple(b[0] for b in blocks[:i + 1]) for i in range(len(blocks))]
        cum = [sum(b[1] for b in blocks[:i + 1]) for i in range(len(blocks))]
        read = 0
        for i, (_, _, marked) in enumerate(blocks):
            if not marked:
                continue
            for j in range(i, max(-1, i - 20), -1):  # lookback
                if keys[j] in self.entries:
                    read = max(read, cum[j])
                    break
        created = 0
        for i, (_, _, marked) in enumerate(blocks):
            if marked and cum[i] >= MIN_CACHEABLE:
                if keys[i] not in self.entries:
                    created = cum[i] - read
                self.entries.add(keys[i])
        return read, max(created, 0), cum[-1]


def old_build_system(a, today):  # layout before the fix, for comparison
    text = bot.INSTRUCTIONS + "\n\n" + bot.athlete_context(a, today) + "".join(f"\n- {f}" for f in a.facts)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def two_segment_build_system(a, today):  # colleague's layout: [instructions][whole tail]
    tail = bot.athlete_context(a, today) + "".join(f"\n- {f}" for f in a.facts)
    return [{"type": "text", "text": bot.INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": tail, "cache_control": {"type": "ephemeral"}}]


def athlete():
    return bot.Athlete(user_id="77", name="Jonas", lang="de", sport="cycling", goal="finish a 160 km gran fondo",
                       facts=["Commutes by bike 2x15 km daily", "Has a smart trainer at home"])


class LayoutTest(unittest.TestCase):
    today = dt.date(2026, 4, 18)

    def test_instructions_block_is_static(self):
        a, b = athlete(), bot.Athlete(user_id="42", name="Marta")
        sa, sb = bot.build_system(a, self.today), bot.build_system(b, self.today + dt.timedelta(days=3))
        self.assertEqual(sa[0], sb[0])
        self.assertEqual(sa[0]["text"], bot.INSTRUCTIONS)

    def test_save_fact_only_appends_blocks(self):
        a = athlete()
        before = bot.build_system(a, self.today)
        a.facts.append("Booked Oetztaler 2026")
        after = bot.build_system(a, self.today)
        strip = lambda bl: [b["text"] for b in bl]
        self.assertEqual(strip(after)[:len(before)], strip(before))
        self.assertIn("cache_control", after[-1])
        self.assertLessEqual(sum("cache_control" in b for b in after), 4)

    def test_no_facts(self):
        s = bot.build_system(bot.Athlete(user_id="1", name="x"), self.today)
        self.assertEqual(len(s), 2)
        self.assertIn("cache_control", s[-1])

    def run_scenario(self, build):
        """msg, save_fact (2 rounds), msg, save_fact (2 rounds), msg -- all inside the TTL."""
        cache, a, tools, log = Cache(), athlete(), bot.select_tools("hi"), []
        log.append(cache.call(build(a, self.today), tools))
        for fact in ["Booked a gran fondo for 2026-09-12", "Prefers indoor intervals on Tuesdays"]:
            log.append(cache.call(build(a, self.today), tools))   # round 1: model calls save_fact
            a.facts.append(fact)
            log.append(cache.call(build(a, self.today), tools))   # round 2: system already has the fact
            log.append(cache.call(build(a, self.today), tools))   # next message
        return log

    def test_memory_write_keeps_prefix_hot(self):
        old, new = self.run_scenario(old_build_system), self.run_scenario(bot.build_system)
        for name, log in (("old", old), ("new", new)):
            print(f"\n{name}: (cache_read, cache_creation, prompt) per call", *log, sep="\n  ")
        # After the first message, every call must read nearly the whole prompt from cache
        for read, created, total in new[1:]:
            self.assertGreaterEqual(read, total - 30)
            self.assertLess(created, 30)
        self.assertTrue(any(c > 900 for _, c, _ in old[1:]))  # the old layout re-cached everything

    def test_two_segments_alone_hit_the_minimum(self):
        # Core tools + instructions are below 1024 tokens, so the instructions marker never
        # writes a cache entry and a rewritten tail still costs the whole prompt.
        log = self.run_scenario(two_segment_build_system)
        print("\ntwo segments:", *log, sep="\n  ")
        self.assertTrue(any(r == 0 and c > 900 for r, c, _ in log[1:]))


if __name__ == "__main__":
    unittest.main()
