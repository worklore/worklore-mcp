# Prompt cache fix

`build_system()` now sends two text blocks, each with an ephemeral cache breakpoint. The first holds only the fixed coaching instructions; the second holds the date and athlete profile, zones, goal, facts, and language. A `save_fact` update changes the second block while leaving the first byte-identical across athletes and calls.

I expanded the fixed coaching reference with guidance consistent with the existing rules. This matters because Claude Sonnet 4.5 requires a 1,024-token prefix for caching, and the old entire cached prompt in `logs/usage.jsonl` was only about 1,000 tokens. A breakpoint on the old instructions alone would likely be too short to cache. The exact prefix token count still needs an API measurement; no API key or live call was used here.

From the colleague's note, the two-breakpoint split, stable static prefix, and usage counters apply. The existing keyword-based tool selection was retained: its tool list can change between messages, which can invalidate the cache prefix, but it stays constant during each message's tool loop. Top-N fact selection was not added. The note's example token counts and claimed savings do not directly apply to this bot.

Verified locally that both breakpoints are present, the instruction block stays identical after a fact is added and across athletes, and only the context block changes. For a live check, compare `cache_read_input_tokens` and `cache_creation_input_tokens` in `logs/usage.jsonl` before and after `save_fact`; after a write, the read should retain the fixed prefix and creation should cover the changed tail. Tool-set changes and cache expiry may also cause misses.
