# Fix: a save_fact no longer evicts the static prompt

## What the log shows

In `logs/usage.jsonl`, every `save_fact` is followed by a **round 2 of the same
message** with `cache_read_input_tokens: 0` and `cache_creation_input_tokens` of
about 1040–1100. That is the whole prefix: the tools, the instructions and the athlete context. There were two causes, plus a
third issue that would have quietly cancelled the obvious fix.

1. **One cache marker over everything.** `build_system` sent instructions and
   athlete context as one block with one `cache_control`. A new fact changes the
   hash of the entire block.
2. **The system prompt was rebuilt on every loop round.** `run_tool` appends the
   fact to `a.facts` in place, and `build_request` called `build_system(a, ...)`
   each round. So round 2 of the same message already carried a different prompt.
3. **The static part is below the cache minimum.** Sonnet 4.5 only caches a
   breakpoint whose prefix (tools + system up to the marker) is at least 1024 tokens.
   Athlete 77's whole prompt was cached at exactly 1024 tokens, so tools plus
   instructions without the ~70-token tail come to about 950. That is under the
   minimum, so a marker after the instructions would be ignored without any error
   and every fact write would still re-create the full prompt.

## What I changed (`bot.py`)

- **`build_system` now returns two blocks, each with `cache_control: ephemeral`**.
  The first is `INSTRUCTIONS`, which is byte-identical for every athlete and every day.
  The second is `athlete_context` (date, profile, zones, goal, facts, language).
  A fact write now invalidates only the tail. The static block is also shared
  across athletes, so one athlete's message keeps it warm for the others.
- **The system prompt is built once per message** in `reply()`, before the tool
  loop. `build_request` now takes the prebuilt `system` instead of `(a, today)`.
  Rounds 2..N of a message are byte-identical to round 1, so they hit the cache
  even after a `save_fact`. The new fact appears from the next message on, which
  is what the README already describes. In round 2 the model still sees the fact
  in its own tool call.
- **`plan_week` moved from the "plan" keyword group into `CORE_TOOLS`.** This adds
  roughly 250 tokens (1046 → 1305 in the log), which puts tools + instructions at
  about 1200, above the 1024 minimum, so the static marker actually gets written.
  It also matches rule 17 ("use plan_week for any weekly structure"), which
  previously pointed at a tool that most messages didn't offer. Keyword filtering
  itself is unchanged: the `race` group (`predict_race`) is still added only on
  keywords, as NOTES.md asks. Side effect: the model can call `plan_week` on any
  message. Cost: about 250 more tokens per call, but read from cache at ~10% price.
  It also means "plan/week/schedule" messages no longer re-create the whole prefix.
  If you'd rather not change the tool set, the other way to clear 1024 is to add
  ~80+ tokens of real, stable content to `INSTRUCTIONS`. Without one of the two,
  the split does nothing on Sonnet 4.5.

An offline check with a fake client (no API calls) confirmed three things. The
request for round 1 and round 2 is identical after a `save_fact`. The static
block is identical for athletes 42 and 77 on different dates. The saved fact
appears in the tail on the next message.

## Not verified

I had no API key and made no API calls, so the token figures come from the
existing log, not from a new measurement. To confirm against the API:

1. Send two messages within 5 minutes. The second should show `cache_read` ≈
   the whole prompt.
2. Send a message that triggers `save_fact`. Round 2 should now *read* from the
   cache; before the fix it created about 1100 tokens.
3. Send the next message. It should show `cache_read` ≈ 1200 (the static prefix)
   and `cache_creation` ≈ 100 (the tail only).

If step 3 shows `cache_creation` near the full prompt, the static prefix is
either still under 1024 tokens or not byte-stable.

## Which parts of the colleague's note applied

- **Applied:** two `cache_control` segments, static instructions first and the
  volatile per-user tail second. INSTRUCTIONS was already free of interpolated
  values, so it is byte-stable.
- **Applied:** keep the tools above the system prompt stable and make the default
  tool selection cover the common case. That is the reasoning behind moving
  `plan_week` to core and leaving `predict_race` keyword-gated.
- **Applied:** load all facts every time and don't select a top-N per message.
  The code already does this, and I left it alone. Capping facts wouldn't have
  helped anyway, as NOTES.md found.
- **Applied:** the verification recipe using `cache_creation_input_tokens` /
  `cache_read_input_tokens`, listed above.
- **Didn't carry over:** "~780 static tokens is fine". The note assumes the
  static segment is cacheable on its own. Here, on Sonnet 4.5 (1024-token
  minimum), it wasn't, and this was the main thing to fix beyond the note.
- **Not in the note:** the system prompt was rebuilt inside the tool loop after an
  in-place fact append. That was a separate cause of the mid-message misses.
- **Not relevant:** the ~55-tool / MCP filtering story (this bot has 4 tools)
  and the Telegram transport.
