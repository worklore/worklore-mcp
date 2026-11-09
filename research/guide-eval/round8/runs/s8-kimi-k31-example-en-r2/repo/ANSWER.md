# Caching fix

Changed `build_system()` in `bot.py` to return two system-prompt text blocks, each with `cache_control: {"type": "ephemeral"}`:

1. `INSTRUCTIONS` only, so the static coaching instructions remain byte-identical across athletes, dates, and memory writes.
2. `athlete_context(a, today)`, containing the date, profile, zones, goal, facts, and language.

After `save_fact` updates the athlete, only the second block changes. The API can therefore reuse the cached static prefix and recreate only the volatile per-athlete tail instead of paying to cache the whole prompt again. Updated `README.md` to describe the two cache boundaries.

## What applied from the colleague's note

- Applied the two-segment prompt-caching fix, with one marker on the stable instructions and one on the volatile context.
- Kept the tool list unchanged within the message's tool loop, preserving the prefix above the system prompt.
- Kept all long-term facts in the context rather than adding per-message top-N selection.
- Retained the existing cache usage logging (`cache_creation_input_tokens` and `cache_read_input_tokens`).
- Left the existing keyword-based tool filtering in place; no aggressive filtering or other unrelated changes were added.

## Verification

Ran the real `reply()` tool-use loop with a local fake LLM and temporary data/log files. Confirmed that two requests were made, both system blocks carried cache markers, `save_fact` changed only the second block, and the static instructions and tools were byte-identical across both requests. No external API request was made.
