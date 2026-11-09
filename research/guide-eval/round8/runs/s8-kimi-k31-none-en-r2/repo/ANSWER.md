# Fix

`build_system()` previously combined the static coaching instructions and the athlete context (including long-term facts) into one system block with a single `cache_control` marker. Every `save_fact` changed that block's text, so the next request could not reuse its cache entry. This matches the zero `cache_read_input_tokens` after memory writes in `logs/usage.jsonl`.

The system prompt is now split into two blocks in `bot.py`:

1. `INSTRUCTIONS`, unchanged between requests, with the ephemeral cache marker.
2. `athlete_context(...)`, without a cache marker, so facts, profile details, and the date can change without invalidating the cached instructions.

`README.md` was updated to describe this behavior.

# Verification

A mocked two-round `reply()` call exercised `save_fact` and confirmed that the cached instructions are byte-identical before and after the write, while the new fact appears only in the uncached athlete-context block. `bot.py` also compiles successfully and `git diff --check` passes. No external API calls were made.
