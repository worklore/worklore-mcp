# Caching fix

## Cause

`build_system()` put the static coaching instructions and mutable athlete context in one cached block. Every `save_fact` changed the long-term facts in that block, so the next request could not reuse the cached instructions and paid to create a new cache entry for the whole prompt.

## Changes

- Updated `build_system()` in `bot.py` to return two system blocks:
  1. The unchanged `INSTRUCTIONS` text, with the `cache_control: {"type": "ephemeral"}` marker.
  2. The athlete context (date, profile, zones, goal, facts, and language), without a cache marker.
- Kept tool selection and memory behavior unchanged. Saved facts still appear in the athlete context on the next tool-loop round and subsequent messages.
- Updated `README.md` to describe the split cache layout.

## Verification

Ran `reply()` locally with a fake LLM and temporary athlete/log files. Across the initial `save_fact` call, its tool-loop continuation, and a follow-up message, the cached instruction block stayed byte-for-byte identical, while only the uncached athlete context gained the saved fact. No external API calls were made.
