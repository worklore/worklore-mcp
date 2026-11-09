# Fix: memory writes no longer evict the static system prompt

## Root cause

`build_system()` in bot.py returned the whole system prompt — coaching
instructions + volatile athlete tail (date, name, zones, goal, facts, language)
— as a **single** text block with one `cache_control: ephemeral` marker. Prompt
caching is a prefix hash: when `save_fact` appended a fact to the athlete record,
the next request's tail changed, the single hash no longer matched, and the
entire prompt (~1000–1100 tokens) was re-created at full price. That is exactly
the pattern in logs/usage.jsonl: every round following a `save_fact` shows
`cache_creation_input_tokens` ≈ the whole prompt and `cache_read_input_tokens: 0`
(e.g. lines 5, 10, 14, 16, 23, 29).

## What I changed

bot.py, `build_system()` only. The system prompt is now an array of two text
blocks, each with its own `cache_control: {"type": "ephemeral"}` marker:

1. Block 1 — the `INSTRUCTIONS` constant plus the `"\n\n"` separator, byte-stable
   across users, days and memory writes (nothing is interpolated into it).
2. Block 2 — `athlete_context(...)`, everything volatile.

The rendered prompt text is unchanged (verified byte-for-byte against the old
layout). No other code was touched: tool selection, the tool loop, and
`log_usage` are as before.

## Effect

A memory write now invalidates only the tail segment; the instructions segment
stays hot. In usage.jsonl, a call right after a `save_fact` should show
`cache_read_input_tokens` covering the instructions block and
`cache_creation_input_tokens` roughly the size of the athlete tail (~100–250
tokens, growing with the fact list) instead of a full-prompt re-creation with
`cache_read_input_tokens: 0`.

## Verification (offline, no API key)

- `python3 -m py_compile bot.py` passes; the module imports without the
  anthropic SDK via its existing fallback.
- Simulated Anthropic prefix-hash caching (chunk per marker): after a simulated
  `save_fact` (fact appended, athlete re-saved, prompt rebuilt) the chunk ending
  at marker 1 is byte-identical and only the chunk ending at marker 2 changes.
- The static chunk is byte-identical across a different athlete and a different
  date.
- `build_request` still assembles normally with the two-block system.

I could not exercise a live API call (no `COACH_ANTHROPIC_KEY` here), so the
usage-log signature above is predicted, not observed.

## Which parts of the colleague's note applied

- **The core fix (their step 1): two `cache_control` segments, static
  instructions first, volatile tail second** — applied as-is; this is the whole
  change. The note's warning about hunting interpolated values in the static
  block applied to the audit of `INSTRUCTIONS` (it is a plain module constant,
  nothing interpolated, so it passes).
- **Their step 2 (keep everything above the system prompt byte-stable; leave
  keyword tool filtering alone)** — applied by not touching it. NOTES.md already
  records keyword tool filtering as a March win, and the note says the
  occasional tool-group change re-creating the cache once per message is
  liveable. This pre-existing behavior is still visible in the log (line 26: a
  `predict_race` message re-created the whole cache) and is out of scope here.
- **Their step 4 (read `usage` in every response)** — already implemented via
  `log_usage`; unchanged.
- **"Resist top-N fact selection / per-message personalization"** — nothing to
  refuse; the bot already injects all facts unconditionally on every message,
  which is what the tail segment now relies on.
- **Not applied:** the note's token figures (~780/~240, ~55 tools, Telegram
  specifics) describe their bot; this bot's split is roughly ~850 static /
  ~200+ volatile tokens with 4 tools, but the mechanics and the 2-of-4-markers
  budget are the same.
