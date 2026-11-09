# Fix: memory writes no longer evict the static system prompt

## The problem

`build_system()` in bot.py returned a single text block carrying one
`cache_control: ephemeral` marker, covering the instructions **and** the
per-athlete tail (date, profile, zones, goal, long-term facts, language).
Prompt caching is prefix-based, so every `save_fact` changed the tail and
invalidated the whole cached block — including the ~1000-token instruction
text that never changes. logs/usage.jsonl shows the pattern: the round right
after a `save_fact` has `cache_read_input_tokens: 0` and pays
`cache_creation_input_tokens` of ~1046–1104 for the full prompt again.

## What I changed

**bot.py — `build_system()`** (bot.py:130): the system prompt is now an array
of two blocks, each with its own `cache_control: {"type": "ephemeral"}`:

1. Block 1: `INSTRUCTIONS` — byte-stable across users, days and memory writes.
2. Block 2: `athlete_context(a, today)` — the volatile tail.

A `save_fact` now changes only block 2's prefix hash, so the next call still
reads block 1 from cache and re-creates only the ~200-token tail. No other
code paths changed: `build_request`, the tool loop and `log_usage` are
untouched, and `log_usage` already records `cache_creation_input_tokens` /
`cache_read_input_tokens`, which is exactly the signal to confirm the fix in
production logs (a memory write should show `cache_read` ≈ the instructions
size and `cache_creation` ≈ the tail size only).

**README.md**: updated the caching paragraph to describe the two-marker
design and the memory-write behavior.

## Verification

No API key/SDK in this environment, so I drove `reply()` with a fake LLM
replaying the failure scenario: round 1 calls `save_fact`, round 2 replies,
then a follow-up message. Data/log files were redirected to a temp dir; the
fixtures were not touched. Assertions, all passing:

- every request has exactly 2 system blocks, both cache-marked;
- the static block is byte-identical across all calls, including after the
  `save_fact`;
- the tail changes only because of the new fact, and is byte-identical on
  the follow-up message (full cache hit in the common case);
- the tools array is byte-stable across rounds.

Before the fix, the same scenario would have made the static block differ on
round 2 (it was part of the single mutated block).

## Which parts of the colleague's note applied

Applied:

- **The core fix: two `cache_control` segments** — static instructions in
  block 1, everything volatile in block 2. This is exactly what was done.
- **Read `usage` to verify** — `log_usage` already records the two cache
  fields; production verification is to watch that a post-`save_fact` call
  shows `cache_read` covering the instructions and `cache_creation` only the
  tail.
- **Refusing top-N / per-message fact selection** — applied by not building
  it: all facts are injected every time, keeping the tail byte-stable across
  messages with no memory write. (The bot's own rule 16 already prevents
  duplicate facts, so the tail grows only with genuinely new facts.)
- **Keep everything above/around the cached blocks byte-stable** — satisfied:
  the tools array is built deterministically and is constant within a
  message's tool loop.

Already in place, so no action needed:

- **Keyword-based tool filtering** — the note presents it as a win and warns
  against over-filtering; this repo already has it (March) and NOTES.md says
  to leave it. Untouched.
- **The tail's "rarest-changing first" ordering** — the note itself calls
  this cosmetic ("after the marker it's one hash anyway"), so I kept the
  existing tail order.

Not applicable:

- The note's Telegram/MCP context and its "~780-token static block" figures —
  the repo is the stdin-transport version, but the mechanism and request
  structure are identical, so the fix transfers directly.
