# Prompt cache fix

Changed `build_system()` in `bot.py` to send two Anthropic text blocks, each with an ephemeral cache marker. The first contains only the byte-stable coaching instructions. The second contains the date and athlete context, including long-term facts. After `save_fact`, only the second block changes, so the static instruction prefix can still be read from cache. Tool selection and tool ordering remain unchanged.

The colleague's two-marker, static-prefix approach applies directly. Their observations about prefix hashing, stable tool schemas, and avoiding per-message fact selection also apply; this bot already loads all facts and filters tools by keyword, so neither needed a change. Their token counts, prices, and savings estimates describe their bot and were not assumed for this one.

Verified locally with a `save_fact` round trip: the instruction block and tool list stayed identical, the athlete block changed and contained the saved fact, and both blocks retained cache markers. `python3 -m py_compile bot.py` passed. Live cache-read and cache-creation token counts require a subsequent API call; no external service was contacted.
