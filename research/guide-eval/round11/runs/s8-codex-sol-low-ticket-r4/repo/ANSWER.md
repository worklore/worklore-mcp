# Prompt caching fix

Changed `build_system()` in `bot.py` to send two text blocks, each with an ephemeral cache marker. The first contains only the fixed coaching instructions. The second contains the date and athlete context, including long-term facts. When `save_fact` changes memory, the static instructions remain byte-identical, so the next request can reuse their cached prefix while creating a new cache entry for the changed context.

The colleague's two-block cache boundary and byte-stable static instructions applied directly. Keeping all facts in a consistent order also applied; the bot already does this. Tool filtering and stable tool order were already implemented, so I left them alone. The quoted token counts, prices, and cache behavior are from the colleague's bot and were not used as measurements for this one.

Verified locally that both blocks have cache markers, a fact write changes only the second block, and `build_request()` sends the split prompt. I did not make a live API call, so actual cache read and creation counts after the change are not measured here; `logs/usage.jsonl` can show those counts during normal operation.
