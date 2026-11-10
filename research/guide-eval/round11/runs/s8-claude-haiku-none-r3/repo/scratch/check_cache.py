import sys, types, datetime as dt
sys.path.insert(0, "/private/tmp/h-YbzoOM")
import bot

scratch = "/tmp/h-YbzoOM/scratch"
bot.ATHLETES_FILE = f"{scratch}/athletes.json"
bot.USAGE_LOG = f"{scratch}/usage.jsonl"
import json
json.dump({"42": {"user_id": "42", "name": "Marta", "facts": []}}, open(bot.ATHLETES_FILE, "w"))

class Block(types.SimpleNamespace):
    def model_dump(self):
        return dict(self.__dict__)

class Usage(types.SimpleNamespace):
    pass

class FakeLLM:
    """Scripted: a message containing 'remember' triggers save_fact, otherwise plain text."""
    def __init__(self):
        self.calls = []
    def create(self, **kw):
        self.calls.append(kw)
        msgs = kw["messages"]
        last = msgs[-1]
        if last["role"] == "user" and isinstance(last["content"], str) and "remember" in last["content"]:
            if not any(m["role"] == "user" and isinstance(m["content"], list) for m in msgs):
                return types.SimpleNamespace(stop_reason="tool_use", content=[
                    Block(type="tool_use", name="save_fact", id="t1", input={"fact": "Owns a Garmin 255"})],
                    usage=Usage(input_tokens=1, cache_creation_input_tokens=0, cache_read_input_tokens=0, output_tokens=1))
        return types.SimpleNamespace(stop_reason="end_turn", content=[Block(type="text", text="ok")],
                    usage=Usage(input_tokens=1, cache_creation_input_tokens=0, cache_read_input_tokens=0, output_tokens=1))

llm = FakeLLM()
print(bot.reply("42", "hello", llm=llm))
print(bot.reply("42", "I remember I own a Garmin 255", llm=llm))
print(bot.reply("42", "how was my week", llm=llm))

sys_calls = [c["system"] for c in llm.calls]
static = [s[0] for s in sys_calls]
assert all(s[0]["cache_control"] == {"type": "ephemeral"} for s in sys_calls), "static block must carry the breakpoint"
assert all("cache_control" not in s[1] for s in sys_calls), "dynamic block must not be cached"
assert all(s[0]["text"] == static[0]["text"] for s in sys_calls), "static block must be byte-identical across calls"
assert "Owns a Garmin 255" not in static[0]["text"], "facts must not be in the cached block"
assert "Owns a Garmin 255" in sys_calls[-1][1]["text"], "saved fact must reach the next request"
print("calls:", len(llm.calls))
print("dynamic block after save:", sys_calls[-1][1]["text"].splitlines()[-3:])
print("ALL CHECKS PASSED")
