# Cache fix

`build_system()` now places the coaching instructions and athlete profile in the cached prefix, with long-term facts in a separate block after the cache boundary. A `save_fact` write changes only that later block, so the next request can reuse the existing prefix instead of recreating the whole prompt cache.

Verified locally that adding a fact leaves the cached block identical, updates the fact block, and keeps the cache marker only on the prefix. `python3 -m py_compile bot.py` passes. Live cache usage was not tested because it requires an API call.
