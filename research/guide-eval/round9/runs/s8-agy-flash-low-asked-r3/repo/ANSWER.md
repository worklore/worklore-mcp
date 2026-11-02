# Changes Made to Fix Prompt Caching

## Root Cause
Previously, `build_system()` combined static coaching instructions (`INSTRUCTIONS`) and volatile athlete data (`athlete_context(a, today)`) into a single text block with one `cache_control: {"type": "ephemeral"}` marker. Because Anthropic prompt caching uses prefix hashing, any modification to athlete data (such as appending a memory fact via `save_fact`) changed the entire block's hash. This evicted the whole cached system prompt, forcing the next API call to pay the full token creation cost (~1000+ tokens) for static instructions that never changed.

## Fix
In [`bot.py`](file:///private/tmp/h-JWDYlu/bot.py), updated `build_system(a, today)` to return two separate text content blocks, each configured with `cache_control: {"type": "ephemeral"}`:
1. **Static Instruction Block**: Contains invariant `INSTRUCTIONS` (~780 tokens) byte-identical across athletes and requests.
2. **Volatile Context Tail**: Contains per-athlete context (`athlete_context(a, today)`, including date, athlete details, and memory facts).

With two cache breakpoints:
- The static instruction block remains cached across requests and users.
- Updates from `save_fact` only invalidate and re-cache the volatile tail block (~240 tokens) instead of evicting the entire system prompt.
