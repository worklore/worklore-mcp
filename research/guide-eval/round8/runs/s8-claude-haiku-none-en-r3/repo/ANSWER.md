# Answer: save_fact evicts the cached system prompt

## Cause

`build_system()` put the whole system prompt into one text block and marked it
`cache_control: ephemeral`. That block contained:

1. the static coaching rules (`INSTRUCTIONS`),
2. the athlete profile (name, zones, goal, language), which is stable,
3. the long-term facts, which `save_fact` appends to, and
4. today's date, which changes daily.

Prompt caching matches the prefix in order (tools, then system, then messages).
Since the facts were inside the cached block, any `save_fact` changed the block,
so the next call missed the cache and paid cache-creation for the whole prefix.
That matches `logs/usage.jsonl` and `NOTES.md`: the call after each save shows
`cache_read_input_tokens: 0` and a fresh `cache_creation_input_tokens`.

## Change (`bot.py`)

- `athlete_profile(a)`: name, sport, zones, goal, language. Stable across `save_fact`.
- `athlete_facts(a, today)`: today's date and the facts list. Volatile.
- `build_system()` now returns two text blocks:
  - block 0: `INSTRUCTIONS` + profile, with `cache_control: ephemeral`
  - block 1: facts and date, no cache marker

A `save_fact` now changes only block 1, which is after the breakpoint, so block 0
still reads from cache. The tool list and messages are untouched.

`README.md` is updated to describe the two blocks.

## Verification

Checked locally without calling the API (no key used, `data/athletes.json` not
written):

- block 0 is byte-identical before and after appending a fact in memory;
- block 1 changes as expected;
- only block 0 carries `cache_control`;
- tools and the request shape are unchanged.

## Open risk: cache minimum

Sonnet only caches a prefix of at least 1024 tokens. My rough estimate for
block 0 plus the core tool definitions is about 800 to 900 tokens, which is close
to or under that limit. Before this change, the facts happened to push the
prefix over the minimum, so caching worked. If block 0 plus tools is under 1024
tokens, the API will not cache it at all and every call will be a full-price
input. I could not check the real count offline.

To confirm after deploying: look at the first few entries in `usage.jsonl`.
Ordinary messages should show `cache_read_input_tokens` near the size of block 0
plus tools. If both `cache_creation_input_tokens` and `cache_read_input_tokens`
stay at 0 for the static part, the prefix is under the minimum. The fix would then
be to add stable content to block 0 (for example, a longer profile section) until
it crosses 1024 tokens. I did not pad the prompt with filler.

## Not changed

- Keyword-based tool selection (`select_tools`) still changes the tool list. A
  message that matches a group such as "plan" or "race" changes the tools prefix,
  which also misses the system cache. `NOTES.md` records that this filtering was a
  deliberate win on tool tokens. Fixing that would mean sending all tools every
  time, which trades cache hits for tool tokens, so I left it as is.
- Nothing was committed, deployed or sent anywhere.
