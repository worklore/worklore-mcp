# Answer: keep the static instructions cached when `save_fact` runs

## Cause

`build_system()` put `INSTRUCTIONS` and the per-athlete context into one text block
with one `cache_control` marker. The cache is a prefix hash, so any change to the
facts (every `save_fact`) changed the hash of the whole block and evicted the
instructions too. `logs/usage.jsonl` shows it: the call after each `save_fact` has
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` around 1,000–1,100.

## What I changed

`bot.py`, `build_system()` now returns two text blocks, each with
`cache_control: {"type": "ephemeral"}`:

1. `INSTRUCTIONS`: static, byte-identical for every athlete and every day.
2. `athlete_context(a, today)`: date, athlete, zones, goal, facts, language.

A memory write now changes only block 2. Nothing else in the file changed. Tools,
tool filtering, `save_athlete`, and logging are untouched.

## What I checked

- `python3 -I /tmp/cachecheck_scratch/check_cache_split.py` (a scratch script outside
  the repo) runs `reply()` with a fake LLM. It saves a fact in round 1, then sends a
  second message. It asserts:
  - two system blocks, both with `ephemeral` markers;
  - block 1 is byte-identical across rounds, across a different athlete and a
    different date;
  - the saved fact appears only in block 2, and only after the save;
  - the tools list does not change within the conversation.
  All assertions pass.
- Not checked against the live API. There is no `COACH_ANTHROPIC_KEY` and the
  `anthropic` SDK is not installed here, so I could not measure cache behaviour or
  token counts.

## Open risk: the 1024-token minimum

Anthropic will not cache a prefix shorter than the model's minimum (1024 tokens for
`claude-sonnet-4-5`), even with a marker on it. The cached prefix at block 1 is the
tools array plus `INSTRUCTIONS`. The log's core-only creation sizes (1024–1104
tokens, which include the athlete tail) suggest that prefix is roughly 1,000 tokens,
right at the line. If it is under 1024, block 1 never gets its own cache entry, and
a `save_fact` will still evict the instructions. The split would then do nothing.

To check after deploying: send a message, call `save_fact`, then send another
message. The message after the save should show `cache_read_input_tokens` close to the
static size, and `cache_creation_input_tokens` close to the athlete tail (about
60–150 tokens). If it shows creation near the full prompt, the static prefix is under
the minimum. The fix then is to make the static prefix longer, for example with more
real coaching guidance. I did not pad it with filler text, since that changes what the
bot is told. This is your call.

## Still not fixed: tool-group changes evict everything

Tools sit above the system prompt in the cached prefix. When a message's keywords add
a tool group, the prefix changes and everything is evicted. The log shows this for
`plan_week` (`cache_creation` 1305) and `predict_race` (1334). The split does not
help there. The fix would mean giving up keyword tool filtering, and NOTES.md says that
filtering saved about 75% of tool tokens. I left that trade-off alone.

## Possible next step (not done)

Within one message's tool loop, a `save_fact` still changes block 2, so the next round
re-creates the tail. That is now small (about 60–150 tokens), so I did not add a fix.
If you want zero re-creation there, take a snapshot of the facts at the start of
`reply()` and apply saved facts from the next message on. The model does not need to
see a fact in the same turn it saved it.

## Colleague's note: what applied

- Applied: two `cache_control` markers, static instructions in block 1 with no
  interpolated values, volatile athlete data in block 2, and the verification idea of
  checking `usage` after a memory write.
- Applied as a warning: "tools sit above the system prompt" applies directly here,
  and the log shows the tool-group evictions.
- Did not apply: top-N fact selection (the bot loads all facts, so nothing to reject).
- Did not apply: the 55-tool filtering story and the Telegram details (not in this
  repo).
- Did not transfer: the note's 780-token static block. Here the static prefix is
  close to the 1024-token minimum, which the note's setup did not have to deal with.
  I could not check this from the note alone.

Nothing has been committed.
