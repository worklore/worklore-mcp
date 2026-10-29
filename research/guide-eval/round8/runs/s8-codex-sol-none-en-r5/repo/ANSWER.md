# Cache fix

`build_system()` now puts the coaching rules and stable athlete profile in a cached
system block. The date and long-term facts are in a following, uncached block.
After `save_fact`, the next tool-loop call sees the new fact while retaining the
same cached prefix. I added stable athlete-record guidance so the prefix remains
above the model's minimum cacheable size even when the mutable facts are excluded.

Tool selection is unchanged. A different selected tool set or an expired cache
entry can still cause a cache creation; a memory write by itself no longer does.

Verified with `python3 -m unittest -v`: tests cover a fact written during a tool
loop, its presence on the next message, and a date change. No API call was made,
so the token savings have not been measured against live usage.
