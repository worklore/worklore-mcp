# Cache fix

`build_system()` now sends two Anthropic text blocks, each with an ephemeral
`cache_control` marker. The first contains only the unchanged coaching
instructions. The second contains the date, athlete profile, zones, goal,
long-term facts, and language. After `save_fact`, the second block changes but
the instruction prefix stays byte-identical and can still be read from cache.

I left keyword-based tool selection in place. Its tool list and order remain
constant across rounds of one message, so this fix does not change that existing
token saving. The existing usage log already records cache creation and read
tokens; no new logging was needed.

From the colleague's note, the two cache boundaries, stable static prefix, and
usage-token verification apply here. The warning about per-message fact
selection also applies: this bot already includes all facts, so there was no
selection logic to remove. Tool filtering was already implemented and was not
part of this change. The note's token counts and claimed price reduction are
specific to that other bot and are not measurements for this one.

Verified locally that a simulated fact write changes only the second system
block, both blocks carry cache markers, and the tools stay identical. Python
compilation passes. Actual `cache_read_input_tokens` after a write still needs
an API call within the cache window; no external service was contacted.
