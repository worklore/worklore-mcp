# Prompt Caching Fix for Memory Writes

## Problem
Previously, `build_system(a, today)` in `bot.py` combined the static coaching instructions (`INSTRUCTIONS`) and the athlete context (`athlete_context(a, today)`, which contains long-term facts, profile, and current date) into a single text block with one `cache_control: {"type": "ephemeral"}` marker.

Because Claude's prompt cache relies on prefix matching, whenever `save_fact` was invoked and appended a new fact to `athlete.facts`, the single system prompt string changed. This invalidated the entire cached prefix, forcing the subsequent API call to pay for creating the cache of the full prompt (~1000+ tokens) rather than reusing the cached static instructions.

## Changes Made
In `bot.py`:
- Updated `build_system(a, today)` to return a list of two distinct text blocks, each configured with `cache_control: {"type": "ephemeral"}`:
  1. **Static Block**: The invariant coaching instructions (`INSTRUCTIONS`), which remain byte-identical across calls and users.
  2. **Volatile Tail Block**: The dynamic athlete context (`athlete_context(a, today)`), containing the date, athlete profile, zones, goal, facts, and language.

## Impact
- When `save_fact` updates an athlete's facts, only the second (volatile tail) block's cache is invalidated and recreated (~240 tokens).
- The first block containing the static instructions (~780 tokens) remains hot in cache (`cache_read_input_tokens`), preventing full-price cache recreation for the static prompt.
