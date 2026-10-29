# Prompt cache fix

`build_system` now sends two text blocks with `cache_control: ephemeral`: the
unchanging coaching instructions first, then the date and athlete context,
including long-term facts. A `save_fact` write changes only the second block, so
the instructions remain an identical cache prefix. The tool list remains fixed
through each message's tool loop.

The colleague's two-marker split applies directly. Its advice to keep tools
stable within a loop also applies; the existing `reply` code already does that.
The note's tool filtering and top-N fact selection changes do not apply here:
tool filtering already exists, and all facts are already included. The existing
`logs/usage.jsonl` records cache creation and read tokens, so no new logging was
needed. Keyword-selected tool sets can still change the prefix between messages.

Verified locally with a simulated `save_fact` tool call: the second request kept
the first marked block byte-identical, changed the second marked block, and
kept the tool list identical. No live Anthropic call was made, so cache token
counts after the change are not yet measured.
