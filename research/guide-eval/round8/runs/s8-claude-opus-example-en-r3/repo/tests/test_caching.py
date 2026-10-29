"""Offline checks that a save_fact does not break the cached system-prompt prefix.

Run: python3 tests/test_caching.py   (no SDK or API key needed)
"""
import json
import os
import sys
import tempfile
import datetime as dt
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bot


class FakeLLM:
    """Round 1 calls save_fact, round 2 answers. Records every request."""
    def __init__(self):
        self.requests = []

    def create(self, **kw):
        self.requests.append(json.loads(json.dumps(kw)))
        usage = NS(input_tokens=0, cache_creation_input_tokens=0, cache_read_input_tokens=0, output_tokens=0)
        if len(self.requests) % 2 == 1:
            block = NS(type="tool_use", id="t1", name="save_fact", input={"fact": "Hates treadmills"},
                       model_dump=lambda: {"type": "tool_use", "id": "t1", "name": "save_fact", "input": {"fact": "Hates treadmills"}})
            return NS(content=[block], stop_reason="tool_use", usage=usage)
        return NS(content=[NS(type="text", text="ok")], stop_reason="end_turn", usage=usage)


def texts(system):
    # cache_control is not part of the cached content; moving it is the documented
    # incremental-caching pattern, so compare the text only.
    return [b["text"] for b in system]


def breakpoints(system):
    return [i for i, b in enumerate(system) if "cache_control" in b]


def main():
    with tempfile.TemporaryDirectory(dir=os.path.dirname(os.path.abspath(__file__))) as tmp:
        bot.ATHLETES_FILE = os.path.join(tmp, "athletes.json")
        bot.USAGE_LOG = os.path.join(tmp, "usage.jsonl")
        bot.save_athlete(bot.Athlete(user_id="1", name="Ana", facts=["Runs at 06:30"]))
        llm = FakeLLM()
        bot.reply("1", "I hate treadmills", llm)   # rounds 1-2, save_fact in round 1
        bot.reply("1", "I hate treadmills", llm)   # next message sees the fact

        r1, r2, r3 = (r["system"] for r in llm.requests[:3])
        assert r1 == r2, "system prompt changed inside one message's tool loop"
        assert texts(r3)[:len(r1)] == texts(r1) and len(r3) == len(r1) + 1, "fact write did not just append one block"
        assert r3[-1]["text"] == "- Hates treadmills"
        assert breakpoints(r3) == [0, 1, len(r3) - 1] and len(breakpoints(r3)) <= 4
        # instructions block must be identical for different athletes and days
        a, b = bot.Athlete(user_id="1", name="Ana"), bot.Athlete(user_id="2", name="Bo", lang="de", facts=["x"])
        assert bot.build_system(a, dt.date(2026, 1, 1))[0] == bot.build_system(b, dt.date(2026, 6, 1))[0]
    print("ok")


if __name__ == "__main__":
    main()
