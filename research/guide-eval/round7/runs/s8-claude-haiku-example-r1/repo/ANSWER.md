# Answer: memory writes evict the static instructions

## Cause

`build_system` returned one text block containing `INSTRUCTIONS` plus the per-athlete
context (date, profile, zones, goal, facts). It carried one `cache_control` marker at
the end. A `save_fact` call changes the facts, which changes the block, and the prompt
prefix hash changes from the first byte of the facts onward. With one marker, that
evicted the instructions along with them. The next call then paid full creation for
the whole prompt. `logs/usage.jsonl` shows this: each call after a `save_fact` has
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` around 1000+.

## Change

`bot.py`, `build_system`: split the system prompt into two text blocks, each with
`cache_control: {"type": "ephemeral"}`.

1. `INSTRUCTIONS`, byte-stable for every athlete and every day (no interpolated values).
2. `athlete_context(a, today)`, the volatile tail.

A memory write now only invalidates block 2. Block 1 and the tools above it should
still hit the cache.

`README.md`: the caching paragraph now describes the two blocks.

Checked offline (no API call): the static block is identical after a `save_fact` and
on the next day, the volatile block does change, and both blocks carry the marker.

## Open risk: the first block may be below the cache minimum

Anthropic ignores a cache breakpoint when the prefix up to it is shorter than the
model's minimum cacheable length. `MODEL` is `claude-sonnet-4-5`, whose minimum is
1024 tokens. The prefix up to block 1 is the tools array plus `INSTRUCTIONS`. My
estimate (chars/4, not a real tokenizer count) is about 730 tokens for the core tools
and instructions, and somewhat more when the planning group is included. That may still
be under 1024. If it is, block 1 is silently not cached. Block 2's breakpoint then
caches the whole prefix again, and a memory write still evicts everything. The split
would be a no-op.

I did not verify this, because it needs a real API call with `COACH_ANTHROPIC_KEY`.
The check is:

- Send a message, then another with a `save_fact` in it. Look at the
  `usage` in `logs/usage.jsonl`.
- If `cache_creation_input_tokens` after the write is about the size of block 2 only
  (~250 tokens), the fix works.
- If it is about the size of the whole prompt, the static prefix is under the minimum.

Fix if it is under: add real static content to `INSTRUCTIONS` until the prefix passes
1024 tokens. This changes model behaviour, so it is your call. I did not pad it.

## Not changed: tool groups also evict the cache

Tools sit above the system prompt in the cached prefix. `select_tools` adds the
`plan` or `race` group when the message contains a keyword, so the tools array changes
and the whole cache misses. The log shows this: the `plan_week` round has
`cache_read_input_tokens: 0`. This is a separate cost from memory writes. The
options are to keep the tool set constant within a conversation, or to accept the
miss because the keyword groups save more than they cost. I left it alone because you
asked about memory writes.

## Colleague's note: what applied

- **Two `cache_control` markers, static instructions first, volatile tail second.**
  Applied. This is the change above.
- **Static block must be byte-stable.** Applied. `INSTRUCTIONS` has no interpolation. I
  added a comment so nobody adds one later.
- **Keep the tools array byte-stable.** Not applied. The keyword tool groups still vary
  the tools per message (see above).
- **Do not do per-message top-N fact selection.** Applied by default. The bot already
  sends all facts, and I did not add any selection.
- **Read `usage` to verify.** Applies, but I could not run it here (see the open risk).
- **Tool filtering saves tokens** and the note's numbers (~75%, ~240-token tail, ~1000+
  whole prompt) are for their setup, not this one. I did not use them.
- **Telegram transport, the 4-marker limit, and the coach-bot details** do not apply to
  this repo. Telegram lives in a separate deploy repo.
