# Prompt cache fix

Changed `build_system()` in `bot.py` to send two text blocks, each with an Anthropic `cache_control: ephemeral` breakpoint. The first contains the byte-stable coaching instructions. The second contains the date and athlete context, including long-term facts. After `save_fact`, only the second block changes, so the first breakpoint can still match the cached static prefix.

The colleague's two-breakpoint approach applies here. Their advice to keep facts consistent between messages also applies: this bot already includes every fact. Tool filtering already exists and was left as it was; its selected schemas stay fixed throughout a message's tool loop. Usage fields are already logged in `logs/usage.jsonl`. No fact ranking or additional tool filtering was added.

Verified locally that both blocks have cache markers, a fact write changes only the second block, and the first block is identical for different athletes. `python3 -m py_compile bot.py` passed. Live cache-read and cache-creation counts were not measured because that requires API calls; confirm the effect from subsequent `logs/usage.jsonl` entries after a memory write.
