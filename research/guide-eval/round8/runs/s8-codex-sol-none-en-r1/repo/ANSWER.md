# Prompt cache fix

`save_fact` used to change the only cached system block because that block held both the coaching rules and the athlete's long-term facts. The next API call therefore created the whole prefix again.

I split the system prompt at the cache breakpoint. The coaching rules and stable athlete profile are in the cached block; the date and long-term facts are in a later, uncached block. A saved fact is still visible on the next tool round and on later messages, but it no longer changes the cached prefix. I added a short, relevant context-handling section to keep the cached prefix above the model's minimum size for the small athlete profiles shown in `logs/usage.jsonl`. Keyword-based tool selection remains in place.

Verification: `python3 -m unittest -v test_bot.py` passes. The regression test saves a fact with a fake LLM, checks that the next request sees it, and checks that the cached block is identical during the tool loop and on the following day. No API call was made, so provider cache usage was not measured; a change in selected tools can still produce a separate cache prefix.
