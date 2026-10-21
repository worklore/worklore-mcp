# Prompt cache fix

`build_system()` now sends two text blocks, each with an ephemeral cache marker. The first contains the unchanged coaching instructions; the second contains the date, athlete profile, and long-term facts. When `save_fact` updates a fact, only the second block changes, so the stable instruction prefix can still be read from cache. Tool selection and the tool loop are unchanged.

Verified locally with assertions that both markers are present, the instruction block remains identical after a fact is added, the athlete block changes, and the selected tools remain identical. `python3 -m py_compile bot.py` also passed. I did not call the Anthropic API, so token savings have not been measured live; the cache-read and cache-creation fields in `logs/usage.jsonl` can confirm the result on the next local run.
