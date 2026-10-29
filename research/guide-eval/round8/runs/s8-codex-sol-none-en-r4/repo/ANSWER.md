# Cache fix

`build_system()` now puts the coaching rules and general context guidance in a
cached system block. The athlete profile, date, and long-term facts are in a
following uncached block. A `save_fact` updates that second block in the next
tool round and message without changing the cached instruction prefix.

The stable guidance also makes the prefix long enough to meet Claude's minimum
cacheable length for this model. Keyword-based tool selection is unchanged;
different selected tool lists can still have separate cache entries because
tools precede the system prompt in the API request.

Verified locally with `python3 -m unittest -v`: both tests pass. They check
that a fact write leaves the cached block identical, updates the athlete context
in the next round and message, and persists to the athlete file. Live cache
usage was not measured because that requires an API call.
