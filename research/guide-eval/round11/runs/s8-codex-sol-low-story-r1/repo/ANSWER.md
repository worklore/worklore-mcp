# Prompt cache fix

Changed `build_system` in `bot.py` to send two text blocks, each with `cache_control: {"type": "ephemeral"}`. The first contains byte-stable coaching instructions; the second contains the date, athlete profile, zones, goal, facts, and language. A `save_fact` write now changes only the second block, allowing the static instructions to remain cached when the tool list is the same.

From the colleague's note, the two-marker split and keeping volatile data after static instructions applied. Its caution about tool stability also applies: tools precede the system prompt in the cache prefix, so a different keyword-selected tool set can still cause a cache miss. I left keyword tool selection intact as requested in `NOTES.md`, and did not add per-message fact selection. The note's tool-token savings and token counts are from another bot and were not assumed here.

Verified locally with a simulated `save_fact`: both blocks have cache markers, the instructions block is identical before and after the write, and the updated fact appears only in the context block. No external API call was made, so actual cache read and creation token counts remain unverified.
