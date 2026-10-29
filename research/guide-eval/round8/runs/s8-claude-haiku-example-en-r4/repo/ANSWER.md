# Fix: memory writes evict the static system prompt

## Cause

`build_system()` returned one text block containing `INSTRUCTIONS` plus the
per-athlete context (date, profile, zones, goal, facts). It had one
`cache_control` marker at the end. The cache is a prefix hash, so when
`save_fact` appended to `athlete.facts`, the block changed and the whole
block, including the instructions that never change, was re-cached. That is
the pattern in `logs/usage.jsonl` and `NOTES.md`: the call after a `save_fact`
shows `cache_read_input_tokens: 0` and `cache_creation_input_tokens` ≈ the
full prompt.

## Change (`bot.py`, `build_system`)

The system prompt is now two text blocks, each with its own
`cache_control: {"type": "ephemeral"}`:

1. `INSTRUCTIONS`: a constant, so it is byte-identical for every athlete and
   every day. A `save_fact` leaves this prefix untouched.
2. `athlete_context(a, today)`: the volatile tail. A `save_fact` or a new day
   re-caches only this block (about 230 characters in the test athlete).

Nothing else changed. The tool list, the keyword tool filter, and the fact
handling are as before.

## Verification

Done offline, without an API call (no key in this environment):

- Built requests before and after appending a fact, and for another athlete
  on another day. Block 1 was identical in all cases; block 2 changed after
  the fact was added. Both blocks carry the `ephemeral` marker. This check was
  a throwaway script and is not in the repo.
- `data/athletes.json` and `logs/usage.jsonl` were not touched.

Not verified: real cache behaviour. Confirm it with the live `usage` numbers.
After a `save_fact`, the next call should show `cache_read_input_tokens` near
the size of block 1 and `cache_creation_input_tokens` near the size of block 2.

## Risk: the static block may be under the minimum cacheable length

Anthropic does not cache a prefix shorter than the model's minimum. For
Sonnet that is 1024 tokens, and the prefix counts from the start of the
request, so it includes the tool definitions. `INSTRUCTIONS` is about 2,500
characters and the core tool schemas add about 400 more, which is probably
around 900 tokens. That is close to the minimum and I could not measure it.
If it is under 1024, the first marker creates nothing, the tail marker covers
the whole prompt, and a `save_fact` still evicts everything. The bug would
remain, silently.

Check: after one normal message, look at the first row in `usage.jsonl` for
that user. If `cache_creation_input_tokens` is about 1024 or more and a later
`save_fact` leaves `cache_read_input_tokens` near the static size, the split
works. If `cache_creation` is only the tail size on the first call, the static
prefix is too short and needs more real content (not padding) to reach the
minimum.

## Other cache costs, not changed

- **Tool keyword filter.** Tools come before the system prompt in the cached
  prefix. A message that adds a group (`plan`, `race` keywords) changes the
  tool list and misses the whole cache for that call. The log shows this:
  the `plan_week` round 1 has `cache_creation_input_tokens: 1305` and
  `cache_read_input_tokens: 0`. `NOTES.md` says to keep the filter because
  it saves about 75% of tool tokens on short messages. That may still be right,
  but it trades off against cache hits. I left it alone.
- **Date in the tail.** The date is in the volatile block, so the tail misses
  once a day. This is cheap, and it is correct that the static block does not
  contain it.

## Colleague's note: what applied

- **Applied:** two `cache_control` markers, one on a byte-stable static block
  and one on the per-athlete tail. This is the core fix.
- **Applied:** keep the static block free of interpolated values. `INSTRUCTIONS`
  has none.
- **Applied:** no per-message fact selection. The bot already sends all facts,
  so nothing to change.
- **Applied (as a check):** read `usage` on every response to confirm the
  behaviour.
- **Partly applied:** keep the tools array byte-stable. The tool list is
  already stable within one message's loop. It still varies across messages
  by keyword, which I left as is (see above).
- **Not applicable:** the Telegram and MCP details, and the 55-tool count (this
  bot has 2 core tools and 2 groups). The ~780/~240 token numbers do not
  match this bot's sizes, so I did not use them.
- **Caution, not applied:** the colleague's static block was about 780 tokens.
  Their note doesn't name the model. If it was a model with a 1024-token
  minimum (Sonnet), a block that size on its own would not cache, so their
  split may also need the check above.
