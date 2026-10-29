# Changes and Analysis

## What Was Changed
In [`bot.py`](file:///tmp/h-umDBfQ/bot.py), updated `build_system(a, today)` to return a list of two separate text blocks with `cache_control: {"type": "ephemeral"}` instead of concatenating the static instructions and volatile athlete context into a single block:

1. **Segment 1 (Static Instructions)**:
   - Text: `INSTRUCTIONS`
   - Cache control: `{"type": "ephemeral"}`
   - Token count: ~780 tokens
   - Byte-identical across all users, messages, and dates.

2. **Segment 2 (Volatile Tail)**:
   - Text: `athlete_context(a, today)`
   - Cache control: `{"type": "ephemeral"}`
   - Token count: ~240–300 tokens
   - Contains dynamic and user-specific elements: date, athlete profile, zones, goal, facts, and language.

Because Anthropic prompt caching works as a prefix hash, previously any change to `a.facts` (via `save_fact`) modified the combined block and caused a cache miss across the entire system prompt (~1000+ tokens). With two cache breakpoints, a change in `a.facts` invalidates only the volatile second block, keeping the static instructions cache hot.

---

## Parts of the Colleague's Note That Applied vs. Ignored

### Applied
1. **Two `cache_control` segments instead of one**:
   - Splitting `system` into two text blocks with `cache_control: {"type": "ephemeral"}`.
   - Block 1: byte-stable static instructions (`INSTRUCTIONS`).
   - Block 2: volatile tail with date, profile, and memory (`athlete_context(a, today)`).
2. **Analysis of prefix-hash prompt caching**:
   - The diagnosis that modifying a fact rewrites the end of the prompt and evicts subsequent/combined cached content.
   - Preserving the static instruction prefix so only the ~240-token tail re-caches on memory updates.
3. **Usage log patterns**:
   - Explaining why `logs/usage.jsonl` showed `cache_read_input_tokens: 0` and full `cache_creation_input_tokens` (~1000+) on round 2 after `save_fact`, and how splitting segments keeps `cache_read` active for the static portion while creating cache only for the tail.

### Ignored / Not Applicable
1. **Tool filtering changes / schema adjustments**:
   - The colleague's note discusses the history of tool filtering by keyword (added in March) and trade-offs of aggressive filtering vs. cache hits. The existing tool filtering in `bot.py` (`select_tools`) was left unchanged as requested in `NOTES.md` ("leave it").
2. **Refusal of Top-N fact selection**:
   - The bot already includes all facts from `a.facts` rather than dynamic subsetting, so no changes or refactoring were needed here.
3. **Telegram long-polling transport / deployment details**:
   - Long-polling transport and deployment instructions live in a separate repo and were not relevant to the prompt caching fix in this repository.
