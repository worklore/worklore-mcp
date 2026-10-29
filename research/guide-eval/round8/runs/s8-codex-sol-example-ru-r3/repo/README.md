# pace-bot

A coaching chat bot on Claude for a small running/cycling club. It is stateless
by design: each message rebuilds the system prompt (coaching rules + the athlete's
profile, zones, goal and long-term facts from `data/athletes.json`), picks the tools
the message might need (`save_fact` and `log_session` always, planning or race tools
when keywords match) and runs a short tool-use loop. `save_fact` is how the bot
remembers durable things an athlete tells it; the next message sees the fact in
its system prompt. Every API call appends its `usage` object to `logs/usage.jsonl`.

Run it locally with `COACH_ANTHROPIC_KEY=sk-ant-... python3 bot.py 42` and type
messages on stdin (the Telegram long-polling transport, which needs
`COACH_TELEGRAM_TOKEN`, lives in a separate deploy repo and just calls `reply()`).
Requires Python 3.11+ and `pip install anthropic`. Prompt caching uses two
`cache_control` markers: one after the stable coaching instructions and one
after the athlete context. A memory write changes the athlete context without
invalidating the cached instructions. Tool-loop rounds and follow-up messages
inside the 5-minute window can read matching prefixes from cache.
