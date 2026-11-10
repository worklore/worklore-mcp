# Prompt cache fix

Changed `build_system()` in `bot.py` to send two text blocks, each with an Anthropic `cache_control: ephemeral` marker. The first contains only the fixed coaching instructions. The second contains the date, athlete profile, zones, goal, facts, and language. A `save_fact` update now changes only the second block, allowing the fixed prefix to remain a cache hit when the tool list is the same.

The colleague's two-breakpoint approach applies here, as does the warning that changing the selected tool schemas can invalidate the prefix. The existing keyword-based tool selection is useful and was left in place. Top-N fact selection does not apply: this bot already includes all facts, and selecting different facts for each message would make the context less cacheable. The usage counters already exist in `logs/usage.jsonl`, so no new logging was needed.

Verified locally that both blocks have cache markers, the instructions block is byte-identical before and after adding a fact, the context block changes, and `build_request()` sends both blocks. `python3 -m py_compile bot.py` passes. No live Anthropic call was made, so actual cache-read and cache-creation counts after this change remain unmeasured. Tool-group changes or cache expiry can still cause a fresh cache creation.
