# Cache fix

`build_system()` now sends the coaching instructions as their own cached text block, followed by an uncached athlete context block. A `save_fact` updates the context on the next API call without changing the cached instruction block. The date and other profile details also remain current.

The existing keyword based tool selection is unchanged. Since Anthropic places tool definitions before the system prompt in its cache prefix, different tool selections can still create separate cache entries. This change addresses the memory write invalidation within a given tool selection.

Verified locally that adding a fact leaves the cached block identical, changes the context block, and keeps the new fact visible. No API call was made, so actual cache usage after the change was not measured.
