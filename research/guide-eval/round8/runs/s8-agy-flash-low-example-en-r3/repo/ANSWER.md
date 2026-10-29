# Prompt Caching Fix for Memory Writes

## Changes Made

In [`bot.py`](file:///tmp/h-Jk882k/bot.py), updated [`build_system`](file:///tmp/h-Jk882k/bot.py#L130-L137) to split the single combined system prompt into two separate text blocks, each with `cache_control: {"type": "ephemeral"}`:

1. **Segment 1 (Static Instructions)**: Contains `INSTRUCTIONS` without any dynamic or per-user interpolation. This segment remains byte-identical across calls, athletes, and dates, keeping its prompt cache hot.
2. **Segment 2 (Volatile Athlete Context Tail)**: Contains `athlete_context(a, today)` which includes the date, profile information, zones, goal, long-term facts, and language.

Because Anthropic's prompt caching relies on prefix matching, isolating the invariant coaching instructions into the first cached segment ensures that updates from `save_fact` (or changes in date/profile) only invalidate and rewrite cache tokens for the tail segment (~240 tokens) rather than evicting the entire system prompt (~1000+ tokens).

---

## Parts of the Colleague's Note That Applied vs. Ignored

### Parts that applied:
- **Two `cache_control` segments instead of one**: Splitting `system` into two text blocks with `cache_control: {"type": "ephemeral"}` where block one is the byte-stable instructions and block two is the volatile tail (date, profile, facts/memory).
- **Keeping static prefix invariant**: Ensuring no dynamic values (like dates or athlete names) are interpolated into the static instruction block.
- **Anthropic 4-marker budget**: Utilizing 2 markers within Anthropic's allowed cache breakpoint limit.

### Parts that were ignored or did not apply:
- **Tool filtering implementation / grouping**: The codebase already had keyword-based tool filtering implemented in March (`CORE_TOOLS` + `TOOL_GROUPS`), which works as intended and was kept as-is.
- **Top-N fact selection**: The codebase did not have top-N fact selection; all athlete facts were already loaded, so no change or rejection of new logic was required here.
- **Telegram polling / MCP specifics**: Not relevant to this core bot repository, which implements direct Anthropic API calls via `reply()`.
