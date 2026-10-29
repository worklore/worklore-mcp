# Prompt cache fix

The old system prompt cached coaching instructions and long-term facts as one
block. `save_fact` changed that block before the next tool round, so the API had
to create a new cache entry for the whole prefix.

I split the system prompt into two cached blocks. The first holds the coaching
rules and stable athlete profile (including zones, goal and language). The second
holds today's date and long-term facts. After a memory write, the first block is
identical and can be read from cache; only the short memory suffix needs a new
cache entry. The second breakpoint still lets unchanged memory be cached across
subsequent calls. Tool selection by keyword is unchanged.

Added regression tests for the cache boundaries after `save_fact` and a date
change. `python3 -m unittest -v test_bot.py` passes (2 tests). No live API call was
made, so actual token usage has not been measured after the change.
