"""Coach bot: a stateless endurance-coaching chat on Claude.

Every incoming message is a fresh request: we rebuild the system prompt from
the athlete record, pick the tools the message might need, and run a short
tool-use loop. Nothing is kept between messages except what is written to
data/athletes.json (the athlete's profile and long-term facts).
"""
import json
import os
import sys
import datetime as dt
from dataclasses import dataclass, field, asdict

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 700
MAX_TOOL_ROUNDS = 5
ATHLETES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "athletes.json")
USAGE_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "usage.jsonl")

# --------------------------------------------------------------------------- LLM
try:
    import anthropic

    class LLM:
        """Thin wrapper so the rest of the file reads the same with or without the SDK."""
        def __init__(self):
            self._client = anthropic.Anthropic(api_key=os.environ["COACH_ANTHROPIC_KEY"])

        def create(self, **kw):
            return self._client.messages.create(**kw)
except ImportError:  # the code is readable and importable without the SDK
    class LLM:
        def __init__(self):
            raise RuntimeError("anthropic SDK not installed: pip install anthropic")

        def create(self, **kw):
            raise RuntimeError("anthropic SDK not installed")

# --------------------------------------------------------------------------- athlete record
@dataclass
class Athlete:
    user_id: str
    name: str
    lang: str = "en"
    sport: str = "running"
    goal: str = "finish a half marathon"
    zones: dict = field(default_factory=lambda: {"Z1": "<135", "Z2": "135-150", "Z3": "150-162", "Z4": "162-172", "Z5": ">172"})
    facts: list = field(default_factory=list)   # long-term memory, grows via save_fact


def _load_all():
    try:
        with open(ATHLETES_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def load_athlete(user_id):
    raw = _load_all().get(str(user_id))
    if raw is None:
        return Athlete(user_id=str(user_id), name="athlete")
    return Athlete(**raw)


def save_athlete(a):
    allrec = _load_all()
    allrec[a.user_id] = asdict(a)
    os.makedirs(os.path.dirname(ATHLETES_FILE), exist_ok=True)
    with open(ATHLETES_FILE, "w") as f:
        json.dump(allrec, f, indent=1, ensure_ascii=False)

# --------------------------------------------------------------------------- system prompt
INSTRUCTIONS = """You are Pace, an endurance coach for recreational runners and cyclists.

Coaching rules:
1. Answer the question that was asked before adding anything else.
2. Keep replies short: a chat message, not an article. Three paragraphs at most.
3. Prescribe training by heart-rate zone or RPE, never by pace, unless the athlete asks for pace.
4. Use the athlete's own zones from the profile below; never invent zone boundaries.
5. Easy days are easy: anything labelled recovery or Z1/Z2 must stay there.
6. Never add more than 10% weekly volume over the previous week.
7. One hard session per week for beginners, two for athletes with 3+ years of training.
8. A rest day is a session. Do not fill it.
9. If the athlete reports pain (not soreness) lasting more than two days, stop the plan and say to see a physio.
10. Do not diagnose injuries or illness. Do not give medication advice.
11. Fuelling: 30-60 g carbs per hour for sessions over 75 minutes; mention it only when relevant.
12. Sleep and stress count as training load. Ask about them when the athlete looks flat.
13. Before a goal race, the last hard session is 7-10 days out. Taper means less volume, same intensity.
14. Do not change the athlete's goal unless they ask. Mention the goal when a question is clearly off-plan.
15. When the athlete tells you something durable about themselves (injury history, schedule, preferences,
    equipment, races booked), call save_fact once with a single sentence. Do not save moods or one-off plans.
16. Do not save a fact that is already in the list below.
17. Use the plan_week tool for any weekly structure; do not write a week by hand.
18. Use log_session when the athlete reports a completed workout, then comment on it.
19. If asked for numbers you do not have (recent volume, last race), ask one question, do not guess.
20. Metric units unless the profile says otherwise.

Tone:
- Warm, direct, no exclamation marks.
- No motivational quotes.
- Address the athlete by first name at most once per reply.
- Reply in the athlete's language from the profile below, even if they write in another language.

Safety:
- Never advise training through chest pain, dizziness or fever.
- Minors: refer to a coach in person.
- If someone asks for weight-loss plans below 1500 kcal per day, decline and suggest a dietitian.

Formatting:
- Plain text. No markdown headings, no tables.
- Lists only for a session structure (warm-up / main / cool-down).
- Numbers with units: 45 min, 12 km, 150 bpm.
"""


def athlete_context(a, today):
    lines = [
        f"Today: {today.isoformat()} ({today.strftime('%A')})",
        f"Athlete: {a.name} (id {a.user_id}), sport: {a.sport}",
        "Zones: " + ", ".join(f"{k} {v}" for k, v in a.zones.items()),
        f"Goal: {a.goal}",
        "Long-term facts:",
    ]
    lines += [f"- {f}" for f in a.facts] or ["- (none yet)"]
    lines.append(f"Language: {a.lang}")
    return "\n".join(lines)


def build_system(a, today):
    # Two cached blocks. The instructions are byte-identical for every athlete and day, so they
    # stay cached when a save_fact write changes the per-athlete tail (date, profile, facts).
    # Keep INSTRUCTIONS free of interpolated values or the first block stops hitting the cache.
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}},
    ]

# --------------------------------------------------------------------------- tools
CORE_TOOLS = [
    {"name": "save_fact", "description": "Remember one durable fact about the athlete.",
     "input_schema": {"type": "object", "properties": {"fact": {"type": "string"}}, "required": ["fact"]}},
    {"name": "log_session", "description": "Record a completed workout.",
     "input_schema": {"type": "object", "properties": {"minutes": {"type": "integer"}, "rpe": {"type": "integer"},
                                                       "note": {"type": "string"}}, "required": ["minutes"]}},
]
TOOL_GROUPS = {
    "plan": (("plan", "week", "schedule", "taper", "build"), [
        {"name": "plan_week", "description": "Draft a week of sessions.",
         "input_schema": {"type": "object", "properties": {"hours": {"type": "number"}, "hard_days": {"type": "integer"}},
                          "required": ["hours"]}}]),
    "race": (("race", "pace", "predict", "finish time"), [
        {"name": "predict_race", "description": "Estimate a finish time from a recent effort.",
         "input_schema": {"type": "object", "properties": {"distance_km": {"type": "number"}, "recent_minutes": {"type": "number"}},
                          "required": ["distance_km"]}}]),
}


def select_tools(text):
    """Core tools always; a group is added only when the message mentions its keywords."""
    tools = list(CORE_TOOLS)
    low = text.lower()
    for _, (keys, group) in TOOL_GROUPS.items():
        if any(k in low for k in keys):
            tools += group
    return tools


def run_tool(a, name, args):
    if name == "save_fact":
        a.facts.append(args["fact"].strip())
        save_athlete(a)
        return "saved"
    if name == "log_session":
        return f"logged {args.get('minutes')} min"
    if name == "plan_week":
        return json.dumps({"hours": args["hours"], "hard_days": args.get("hard_days", 1), "sessions": ["Mon rest", "Tue Z2 45 min", "..."]})
    if name == "predict_race":
        return json.dumps({"distance_km": args["distance_km"], "estimate_min": round(args.get("recent_minutes", 50) * 2.1)})
    return f"unknown tool {name}"

# --------------------------------------------------------------------------- the per-message loop
def log_usage(usage, user_id, round_no, tool=None):
    rec = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "user": user_id, "round": round_no,
           "input_tokens": usage.input_tokens, "cache_creation_input_tokens": usage.cache_creation_input_tokens,
           "cache_read_input_tokens": usage.cache_read_input_tokens, "output_tokens": usage.output_tokens}
    if tool:
        rec["tool"] = tool
    os.makedirs(os.path.dirname(USAGE_LOG), exist_ok=True)
    with open(USAGE_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def build_request(a, messages, tools, today):
    return {"model": MODEL, "max_tokens": MAX_TOKENS, "system": build_system(a, today), "tools": tools, "messages": messages}


def reply(user_id, text, llm=None):
    llm = llm or LLM()
    a = load_athlete(user_id)
    today = dt.date.today()
    tools = select_tools(text)
    messages = [{"role": "user", "content": text}]
    for round_no in range(1, MAX_TOOL_ROUNDS + 1):
        resp = llm.create(**build_request(a, messages, tools, today))
        used_tools = [b.name for b in resp.content if b.type == "tool_use"]
        log_usage(resp.usage, a.user_id, round_no, tool=",".join(used_tools) or None)
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")
        messages.append({"role": "assistant", "content": [b.model_dump() for b in resp.content]})
        results = [{"type": "tool_result", "tool_use_id": b.id, "content": run_tool(a, b.name, b.input)}
                   for b in resp.content if b.type == "tool_use"]
        messages.append({"role": "user", "content": results})
    return "Sorry, I lost the thread. Ask me again?"


if __name__ == "__main__":
    # Local chat: python3 bot.py <user_id>; Telegram long-polling lives in telegram.py (not in this repo).
    uid = sys.argv[1] if len(sys.argv) > 1 else "42"
    for line in sys.stdin:
        print(reply(uid, line.strip()))
