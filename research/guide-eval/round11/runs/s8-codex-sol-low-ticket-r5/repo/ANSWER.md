# Prompt cache fix

`bot.py` now sends two cached system text blocks: fixed coaching instructions first, then the athlete context (date, profile, zones, goal, facts and language). A `save_fact` changes the second block while leaving the first block byte-identical. I added fixed coaching guidance to make the first cache breakpoint more likely to meet Claude Sonnet 4.5's 1,024-token minimum; a shorter marked prefix is not cached at all.

The colleague's two-breakpoint, stable-prefix approach applied. The warnings about changing tools also applied, so tool selection and ordering were left alone. Fact selection did not apply as a change: this bot already loads all facts. The suggested tool filtering was already present and was left alone.

Local checks confirmed that a fact change leaves the first system block and selected tools unchanged, changes only the athlete block, and that `bot.py` compiles. No API call was made, so actual cache hits and token counts still need confirmation from `logs/usage.jsonl`: after a `save_fact`, expect a nonzero `cache_read_input_tokens` for the fixed prefix and a smaller `cache_creation_input_tokens` for the changed tail. The exact split depends on Anthropic's tokenization and cache lifetime.

Reference: [Anthropic prompt caching documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).
