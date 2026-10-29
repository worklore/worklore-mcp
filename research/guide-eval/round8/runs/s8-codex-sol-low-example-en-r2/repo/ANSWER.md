# Cache fix

Changed `build_system` in `bot.py` to send two text blocks, each with `cache_control: {"type": "ephemeral"}`. The first contains only the fixed coaching instructions. The second contains the date, athlete profile, zones, goal, facts, and language. A `save_fact` write now changes the second block while leaving the first cacheable prefix byte-identical.

The colleague's two-marker split and prefix-stability reasoning applied directly. Its advice to keep all facts in the context and to avoid changing tool selection for this fix also applied: this bot already loads every fact, and `NOTES.md` says the existing keyword-based tool filtering is useful. The note's tool-filtering optimization itself was already present, so I made no change to it. The quoted token counts, prices, and live cache results are from another bot and were not assumed for this one.

Verified locally that a memory write changes only the second block and that both blocks carry cache markers. I did not make an API call, so actual cache read and creation token counts after this change remain unmeasured. `logs/usage.jsonl` will show those counts on subsequent calls.
