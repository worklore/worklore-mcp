# Answer

## What changed

`build_system()` in `bot.py` (the function behind every API call's `system`
parameter) previously concatenated the static `INSTRUCTIONS` with the
per-athlete tail (`athlete_context`: date, name, zones, goal, long-term facts,
language) into a single text block carrying one `cache_control` marker.
Anthropic's prompt cache is a prefix hash, so every `save_fact` call — which
appends a fact to the tail — changed the block and evicted the entire cached
prompt, instructions included. That is exactly the pattern in
`logs/usage.jsonl`: every round following a `save_fact` shows
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` back at
~1000–1100 (full prompt) instead of just the size of the changed tail.

The fix is the two-segment cache from the colleague's note:

- `system` is now an array of two text blocks, each with its own
  `cache_control: {"type": "ephemeral"}` breakpoint (bot.py:130-137).
- Block 1: the static `INSTRUCTIONS` plus the `"\n\n"` separator. It is a
  module-level constant with no interpolated dates, names, or counters, so it
  is byte-identical across users, days, and memory writes, and it stays hot
  in the cache.
- Block 2: the volatile per-athlete tail from `athlete_context()`. A memory
  write now re-creates only this block (~100–250 tokens) instead of the whole
  ~1000-token prompt.

The rendered prompt text is byte-for-byte identical to before, so model
behavior is unchanged; only the cache segmentation differs. `README.md`'s
caching paragraph was updated to describe the two breakpoints.

Verified offline (no API calls, per the ground rules): two blocks with
ephemeral markers; block 1 byte-identical across athletes and dates; a
simulated `save_fact` changes only block 2; rendered text matches the old
single-block assembly; and an end-to-end `reply()` run with a stub LLM
confirms round 2 after a write still sends the identical static block with
the new fact in the tail.

Expected effect in `logs/usage.jsonl` going forward: within the 5-minute TTL,
rounds after a `save_fact` should show `cache_read_input_tokens` covering the
instruction block and `cache_creation_input_tokens` at roughly the tail size,
instead of `cache_read: 0` plus full-prompt `cache_creation`.

## Which parts of the colleague's note applied

- **The core fix** — two `cache_control: ephemeral` markers instead of one,
  static instructions as segment one, per-user volatile tail as segment two.
  Applied verbatim; it maps directly onto this codebase's `INSTRUCTIONS` /
  `athlete_context` split.
- **Byte-stability of the static block** — treated as a hard requirement and
  verified: `INSTRUCTIONS` has no interpolation, and the `"\n\n"` separator
  was kept inside block 1 so the split introduces no new bytes.
- **Reading `usage` on every response** — `log_usage()` already does this;
  `cache_creation_input_tokens` / `cache_read_input_tokens` remain the
  verification signal.
- **The tools-array caveat** — applied as "leave it, it's liveable". The
  `tools` array sits above the system prompt in the cached prefix, so a
  message that pulls in the `plan` or `race` tool group re-creates the whole
  prefix once (visible in the log at 06:44 and 08:04). `NOTES.md` records the
  keyword filtering as a clear win and says to leave it; within one message's
  tool loop the tool list is constant, which is where the cache pays most.
- **Resisting per-message top-N fact selection** — applied by not building
  anything: the bot already injects all facts every time, which is the
  cache-friendly choice. No selection logic was added.

## Which parts did not apply

- **Telegram/MCP transport details** — this repo only has the local stdin
  loop; the transport lives elsewhere. Irrelevant here.
- **Implementing keyword-based tool filtering as a new win** — already
  present in this codebase (added in March, per `NOTES.md`); nothing to do.
- **Tail ordering "rarest-changing first"** — the note itself concedes this
  is cosmetic ("after the marker it's one hash anyway"), so the existing
  `athlete_context` order was kept to minimize churn.
- **Live verification against the API** — not performed: no key in this
  environment and the ground rules forbid external calls. Verification was
  done on the assembled request shape instead; the usage-log check from the
  note's "Verify" section can be run in production once deployed.
