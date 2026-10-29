"""Offline check that a save_fact only appends to the cached prefix.

FakeLLM models Anthropic's prompt cache closely enough for this: entries are written
at cache_control markers (if the prefix reaches MIN_TOKENS), and a lookup walks back
over up to 20 earlier block boundaries. Tokens are approximated as len(json)/4.
Run: python3 -m unittest discover tests
"""
import copy, datetime as dt, json, os, sys, tempfile, types, unittest

sys.path.insert(0, os.environ.get("BOT_DIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bot

MIN_TOKENS = 1024        # Sonnet 4.5 minimum cacheable prefix
TOOL_OVERHEAD = 184      # tool-use system prompt the API adds; calibrated so athlete 42 = 1046 as in logs/usage.jsonl


def _strip(block):
    b = dict(block); b.pop("cache_control", None); return b


class FakeLLM:
    def __init__(self, script):
        self.cache, self.script, self.usages = set(), list(script), []

    def create(self, **kw):
        # Prefix order is tools -> system; each system block is a boundary.
        units = [json.dumps(kw["tools"])] + [json.dumps(_strip(b)) for b in kw["system"]]
        marks = [False] + ["cache_control" in b for b in kw["system"]]
        size = lambda n: sum(len(u) for u in units[:n]) // 4 + TOOL_OVERHEAD
        key = lambda n: hash(tuple(units[:n]))
        last = max(i for i, m in enumerate(marks) if m) + 1
        read = 0
        for n in range(last, max(0, last - 20), -1):
            if key(n) in self.cache:
                read = size(n); break
        for i, m in enumerate(marks):
            if m and size(i + 1) >= MIN_TOKENS:
                self.cache.add(key(i + 1))
        usage = types.SimpleNamespace(input_tokens=0, output_tokens=0, cache_read_input_tokens=read,
                                      cache_creation_input_tokens=size(last) - read if size(last) >= MIN_TOKENS else 0)
        self.usages.append(usage)
        content = self.script.pop(0)
        stop = "tool_use" if any(b.type == "tool_use" for b in content) else "end_turn"
        return types.SimpleNamespace(content=content, usage=usage, stop_reason=stop)


def _tool(name, **inp):
    return types.SimpleNamespace(type="tool_use", id="t1", name=name, input=inp,
                                 model_dump=lambda: {"type": "tool_use", "id": "t1", "name": name, "input": inp})


def _text(t):
    return types.SimpleNamespace(type="text", text=t, model_dump=lambda: {"type": "text", "text": t})


class CacheLayout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        bot.ATHLETES_FILE = os.path.join(self.tmp, "athletes.json")
        bot.USAGE_LOG = os.path.join(self.tmp, "usage.jsonl")
        # Athlete 42 as in data/athletes.json (3 facts), the record behind logs/usage.jsonl.
        bot.save_athlete(bot.Athlete(user_id="42", name="Marta", goal="sub-1:55 half marathon in June",
                                     zones={"Z1": "<138", "Z2": "138-152", "Z3": "152-164", "Z4": "164-174", "Z5": ">174"},
                                     facts=["Runs before work, 06:30, Mon/Wed/Fri",
                                            "Left achilles tendinopathy in 2024, fully recovered", "Owns a Garmin 255"]))

    def test_save_fact_only_appends(self):
        a = bot.load_athlete("42")
        today = dt.date(2026, 4, 18)
        before = bot.build_system(a, today)
        a.facts.append("Owns a Garmin 255")
        after = bot.build_system(a, today)
        self.assertEqual([_strip(b) for b in before], [_strip(b) for b in after[:len(before)]])
        self.assertEqual(len(after), len(before) + 1)
        self.assertLessEqual(sum("cache_control" in b for b in after), 4)

    def test_memory_write_recaches_only_the_new_fact(self):
        llm = FakeLLM([[_text("hi")],                                        # msg 1
                       [_tool("save_fact", fact="Has a race on 2026-06-07")],  # msg 2, round 1
                       [_text("noted")],                                     # msg 2, round 2
                       [_text("ok")]])                                       # msg 3
        bot.reply("42", "hello", llm=llm)
        bot.reply("42", "I booked a half in June", llm=llm)
        bot.reply("42", "thanks", llm=llm)
        full = llm.usages[0].cache_creation_input_tokens
        after_write = llm.usages[2]
        self.assertGreater(after_write.cache_read_input_tokens, 0)
        self.assertLess(after_write.cache_creation_input_tokens, 0.1 * full)
        self.assertEqual(llm.usages[3].cache_creation_input_tokens, 0)
        for u in llm.usages:
            print(f"read={u.cache_read_input_tokens:5d} create={u.cache_creation_input_tokens:5d}")


if __name__ == "__main__":
    unittest.main()
