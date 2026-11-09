# Fix: memory writes no longer evict the static system prompt

## What was wrong

`build_system()` in `bot.py` sent the system prompt as a single text block
with one `cache_control: {"type": "ephemeral"}` marker, containing the static
coaching instructions **and** the volatile per-athlete tail (date, profile,
zones, goal, long-term facts, language). Prompt caching is prefix-based: when
`save_fact` appended a fact, the whole block's hash changed, so the next call
in the tool loop re-created the entire ~1000-token prompt at full price and
read nothing from cache. `logs/usage.jsonl` shows the signature: every round
right after a `save_fact` has `cache_read_input_tokens: 0` and
`cache_creation_input_tokens` back at ~1000-1100 (e.g. the 06:43:16,
08:02:33 and 08:05:39 rounds on 2026-04-18), while rounds not preceded by a
memory write read the full prompt from cache.

## What I changed

- `bot.py` — `build_system()` now returns **two** text blocks, each with its
  own `cache_control: {"type": "ephemeral"}` marker:
  1. Block 1: the `INSTRUCTIONS` constant, byte-stable across athletes and
     days (no interpolated dates, names, or counters).
  2. Block 2: `athlete_context()` — the volatile tail.

  After a memory write, only the tail's hash changes; the instructions stay
  hot in the cache, so the re-creation cost drops from the whole prompt to
  the ~60-token tail. Block 2 keeps its existing order and keeps including
  **all** facts on every call (no per-message selection).
- `README.md` — updated the caching paragraph, which still described a
  single marker.

Nothing else changed: tool keyword filtering, the tool-use loop, and the
usage logging are untouched.

## Verification (no network calls)

Per the ground rules I did not call the external API. Instead I exercised
the real code path — `reply("42", ..., llm=FakeLLM())` with a fake LLM that
emits a `save_fact` tool_use in round 1 and text in round 2 — and asserted on
the recorded requests:

- `system` is a two-block list and every block carries an ephemeral marker.
- Block 1 is byte-identical between round 1 (before the write) and round 2
  (after the write), and equals `INSTRUCTIONS` exactly.
- Block 2 differs only by the one new fact line.
- The `tools` array is byte-identical within the message's loop.
- All existing facts are present in the tail (include-everything preserved).

All checks passed. `data/athletes.json` and `logs/usage.jsonl` were backed up
before the run and restored after, so no test artifacts remain.

Expected effect in production, per the note's verify section: after a
`save_fact`, the next call should show `cache_read_input_tokens` covering the
instructions block and `cache_creation_input_tokens` roughly the size of the
tail only — not the full prompt.

## Which parts of the colleague's note applied

Applied:

- **The core fix (step 1): two `cache_control` markers instead of one** —
  static instructions as segment 1, volatile per-user tail as segment 2.
  This is the entire fix.
- **Keep everything above the system prompt byte-stable (step 2)** — kept
  as-is; the bot's keyword tool filtering was already in place and the tool
  list is constant within a message's tool loop, which is where caching pays
  most. No change needed.
- **Resist per-message personalization (step 3)** — applied by *not building*
  anything: the bot already injects all facts on every message, so the tail
  is stable per athlete and the tail cache can hit. I kept that.
- **Read `usage` in every response (step 4)** — already implemented via
  `log_usage()`; unchanged. It is also what made the original diagnosis
  possible.

Did not apply / not applicable:

- The tool-filtering win (~75% fewer tool tokens) — already shipped in this
  repo in March (see NOTES.md); there was nothing to do.
- The note's token figures (~780 static / ~240 tail) and its Telegram/MCP
  specifics describe that deployment; this repo's prompt is ~1000 tokens
  total and has no MCP servers. Only the mechanism transferred.

The note's diagnosis matched this repo exactly, including the symptom in
`logs/usage.jsonl` it told us to look for.
