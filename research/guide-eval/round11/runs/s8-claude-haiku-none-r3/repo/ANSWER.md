# Fix: `save_fact` evicting the static instructions from the prompt cache

## Cause

`build_system()` put the coaching instructions and the per-athlete context
(zones, goal, today's date, long-term facts) into one text block with the
`cache_control` marker. A `save_fact` call changes the facts list, so the cached
text changed, and the next request missed the cache and wrote the whole prefix again.

`logs/usage.jsonl` shows it: the request right after each `save_fact` has
`cache_read_input_tokens: 0` and a fresh `cache_creation_input_tokens` of about
1000+. The save happens in round 1, so round 2 pays the write, and the next user
message pays it again.

## Change (`bot.py`, `build_system`)

The system prompt is now two blocks:

1. `INSTRUCTIONS`, identical for every athlete and every day, with
   `cache_control: ephemeral`. This is the cached prefix.
2. `athlete_context(a, today)`, no cache marker. It holds the facts, zones, goal
   and date, which are the parts that change.

A `save_fact` now changes only block 2, and block 1 still reads from cache. The
date moved into block 2 too, so the instructions no longer change at midnight.

`README.md`: the caching paragraph now describes the two-block layout.

## Verification

- `scratch/check_cache.py` (outside the repo, in `/tmp/h-YbzoOM/scratch/`) runs
  `reply()` through a fake LLM with a `save_fact` turn. It redirects the athlete and
  usage files to scratch, so `data/` and `logs/` are untouched. It checks that:
  - block 1 has the cache marker and is byte-identical across all calls, including
    the ones before and after the save;
  - block 2 is not cached;
  - the saved fact appears in block 2 of the next request, and not in block 1.
  Result: all checks pass.
- I did not call the Anthropic API, so this does not show real cache hits.

## Open risk: the cached prefix may be under the minimum

Caching only applies when the cached prefix is at least 1024 tokens for Sonnet-class
models (please check the current docs). Below that, the marker is silently ignored.
Before this change, the prefix was tools + instructions + athlete context. The log
shows it at about 1024–1100 tokens with core tools, so it was just over the minimum.

After this change the cached prefix is tools + instructions only. My rough estimate
is about 850–950 tokens for the instructions plus core tools, which may be under
1024. If so, caching would stop working on every call, not only after `save_fact`.
I could not measure the exact count: there is no local tokenizer, and I did not call
the API.

How to check after a deploy: the first call of a conversation should show
`cache_creation_input_tokens > 0`, and the next call `cache_read_input_tokens > 0`.
If both stay at 0, the instructions are under the minimum. The fix then needs about
150–300 more tokens of stable content in `INSTRUCTIONS`, or fewer requests with
the tool-group variants (see below). I did not pad the prompt, since that changes
the bot's behaviour and I cannot measure the gap.

## Not changed: tool sets split the cache

`select_tools()` adds the `plan` and `race` tools on keyword match. The tool list
comes before the system prompt in the cached prefix, so each distinct tool set has
its own cache entry. A message with "plan" in it will write its own prefix rather
than read the core-tools entry. The log shows this (`plan_week` calls write about
1305 tokens). This predates the change and is separate from the `save_fact` problem.
If the prefix-size risk above is real, always sending the full tool list would be
the simplest way to get one cache entry. That trades away the March keyword-filter
saving, so I left it for you to decide.

## Files

- `bot.py`: `build_system()` returns two blocks.
- `README.md`: the caching paragraph.
- `ANSWER.md`: this file.
- Not committed.
