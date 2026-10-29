"""Offline check of prompt-cache behaviour, no API calls.

Mimics Anthropic prefix caching: the prefix is tools + system blocks; a write
happens at the block carrying cache_control, a read is looked up at that block
and at up to 20 earlier block boundaries. Prefixes under MIN_TOKENS are not
cached. Tokens are estimated as chars/2.95 (calibrated so athlete
cached prefixes land near the ~1050 tokens seen in logs/usage.jsonl), so absolute numbers are rough; what
matters is whether a save_fact makes the next call re-create the whole prompt.

    python3 -I tests/sim_cache.py
"""
import hashlib, json, os, sys, types, datetime as dt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bot

MIN_TOKENS, LOOKBACK = 1024, 20
tok = lambda s: round(len(s) / 2.95)


class FakeLLM:
    def __init__(self):
        self.cache = set()

    def create(self, system, tools, messages, **_):
        pieces = [json.dumps(tools)] + [b["text"] for b in system]
        bounds, acc = [], ""
        for p in pieces:
            acc += p
            bounds.append((hashlib.sha256(acc.encode()).hexdigest(), tok(acc)))
        marks = [i + 1 for i, b in enumerate(system) if "cache_control" in b]
        read = 0
        for m in marks:
            for j in range(m, max(0, m - LOOKBACK) - 1, -1):
                if bounds[j][0] in self.cache:
                    read = max(read, bounds[j][1]); break
        top = max(marks)
        creation = 0
        if bounds[top][1] >= MIN_TOKENS:
            for m in marks:
                if bounds[m][1] >= MIN_TOKENS:
                    self.cache.add(bounds[m][0])
            creation = bounds[top][1] - read
        else:
            read = 0
        uncached = bounds[-1][1] - read - creation
        self.usage = dict(cache_read=read, cache_creation=creation, uncached=uncached)
        last = messages[-1]["content"]
        if isinstance(last, str) and last.startswith("remember:"):
            content = [types.SimpleNamespace(type="tool_use", name="save_fact", id="t1", input={"fact": last[9:]},
                                             model_dump=lambda: {"type": "tool_use", "id": "t1", "name": "save_fact", "input": {}})]
            stop = "tool_use"
        else:
            content, stop = [types.SimpleNamespace(type="text", text="ok")], "end_turn"
        u = types.SimpleNamespace(input_tokens=uncached, cache_creation_input_tokens=creation,
                                  cache_read_input_tokens=read, output_tokens=1)
        return types.SimpleNamespace(content=content, stop_reason=stop, usage=u)


def main():
    import tempfile, shutil
    tmp = tempfile.mkdtemp()
    shutil.copy(bot.ATHLETES_FILE, os.path.join(tmp, "athletes.json"))
    bot.ATHLETES_FILE = os.path.join(tmp, "athletes.json")
    log = []
    bot.log_usage = lambda usage, uid, rnd, tool=None: log.append((rnd, tool, usage.cache_read_input_tokens,
                                                                  usage.cache_creation_input_tokens, usage.input_tokens))
    llm = FakeLLM()
    for msg in ["hi", "how was my run", "remember: Has a 10k event on May 3", "thanks", "remember: Prefers trails", "ok"]:
        bot.reply("42", msg, llm=llm)
    print(f"{'round':>5} {'tool':>10} {'read':>6} {'create':>6} {'input':>6}")
    for r in log:
        print(f"{r[0]:>5} {str(r[1]):>10} {r[2]:>6} {r[3]:>6} {r[4]:>6}")
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
