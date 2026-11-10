# Answer: keep the static instructions cached through `save_fact` writes

## Cause

`build_system()` returned one text block: `INSTRUCTIONS + athlete_context(...)`, with a single
`cache_control` marker at the end. The cache is a prefix hash, so any change in the athlete
tail (a new fact, a new day) changes the hash of the whole block. `logs/usage.jsonl` shows it:
after each `save_fact`, the next call has `cache_read_input_tokens: 0` and
`cache_creation_input_tokens` back to the full prompt size (about 1050).

## What changed

- `bot.py`, `build_system()`: the system prompt is now two text blocks, each with
  `cache_control: ephemeral`.
  - Block 1 is `INSTRUCTIONS` only. It is byte-identical for every athlete and every day.
  - Block 2 is `athlete_context()`: date, athlete, zones, goal, facts, language.
  - A `save_fact` or a day change now re-caches only block 2. The static prefix stays hot.
- `tests/test_cache_split.py` (new): offline unit tests. They check the two-marker layout,
  that block 1 is identical across athletes and days, that a fact write changes only block 2,
  and that block 1 contains no interpolated values. Run with
  `python3 -m unittest tests/test_cache_split.py`. All 4 pass.
- `README.md`: the caching paragraph now describes the two-block layout.

Nothing else changed. The tools, the tool loop, and the usage log are the same. The only
request change is that `system` is now a list of two blocks instead of one.

## Colleague's note: what applied and what didn't

Applied:
- Two `cache_control: ephemeral` markers, instructions first, per-user tail second. This is the
  core of the change.
- Keep block 1 free of interpolated values (dates, names, counters). The test enforces this.
- Read `usage` on each response to verify (see below).

Did not apply, or already in place:
- Top-N fact selection per message. The bot already loads all facts every time, so there is
  nothing to change.
- Tool filtering. It was already done by keyword in March (see `NOTES.md`), so I left it alone.
- The "4 markers" point. We use 2, which is enough.

Did not carry over: the note's numbers (about 780 static tokens) are for its own prompt. Ours
is smaller, and that matters, as described next.

## Risk: the 1024-token minimum (not verified live)

Anthropic only caches a prefix that is at least 1024 tokens long for Sonnet models
(`MODEL = "claude-sonnet-4-5"`). The cacheable prefix for block 1 is the tool definitions
plus `INSTRUCTIONS`. Their size, estimated from the character counts and calibrated against the
logged `cache_creation_input_tokens: 1046`, is roughly 950–1000 tokens for the default core
tools. That is just under the minimum.

Consequences:
- If block 1 is under 1024 tokens, the first marker creates no cache entry. Block 2's marker
  then caches the whole prefix, as before. In that case a memory write still re-creates the
  whole prompt, so the change gains nothing. It does no harm either.
- Adding a `plan` tool group changes the tool list and goes over the minimum. Tool-group changes
  also evict the cache, because tools come before the system prompt (see below).

Recommended next step: grow `INSTRUCTIONS` by a few hundred characters of real guidance. This
is a content decision, so I did not pad it. Then check the logs.

## How to verify (needs the live API; I could not run it here)

Send two messages within 5 minutes, then one `save_fact` message, then one more message. Expect:
- Message 2: `cache_read_input_tokens` covers the whole prompt.
- After `save_fact`: `cache_read_input_tokens` covers block 1 (about 1000 or more if the minimum
  is met), and `cache_creation_input_tokens` is about the size of block 2 (about 250 characters,
  roughly 80–100 tokens), not the full prompt.

If `cache_creation` is still the full prompt size, either block 1 is under the minimum (see
above) or something in block 1 changes per request. The offline tests guard against the second
case.

## Not changed: other eviction sources

- Tool groups. `select_tools()` changes the `tools` array per message. Tools come before the
  system prompt in the cache prefix, so a message that adds the `plan` or `race` group re-caches
  everything (for example the `plan_week` row in the log: `cache_creation` 1305). This is a
  separate, known trade-off (`NOTES.md`). Fixing it would mean sending all tools every time,
  which the March change was meant to avoid. I left it for you to decide.
- Daily date change: block 2 re-caches once per day. This is expected.
