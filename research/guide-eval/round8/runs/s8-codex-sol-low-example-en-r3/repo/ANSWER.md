# Prompt cache fix

Changed `build_system()` in `bot.py` to send two text blocks with `cache_control: {"type": "ephemeral"}`. The first contains only the constant coaching instructions; the second contains the date and athlete context, including long-term facts. A `save_fact` write now changes the second block while leaving the first block byte identical, so the static prefix can remain cached.

The colleague's two-breakpoint approach applies directly. Their advice to keep the tool list stable within a request also applies; this bot already selects tools once before its tool loop, so no tool change was needed. The bot already includes all facts and logs cache creation and read token counts, so those suggestions required no change. The note's tool-filtering optimization had already been implemented and was left intact.

Verified locally that both blocks have cache markers, a new fact changes only the second block, and the selected tools retain their order. `python3 -m py_compile bot.py` passed. No live Claude request was made, so cache-read and cache-creation token counts after this change have not been measured.
