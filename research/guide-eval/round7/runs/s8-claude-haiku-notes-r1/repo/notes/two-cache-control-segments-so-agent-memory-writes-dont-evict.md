---
title: Two cache_control segments so agent memory writes don't evict the whole Claude system prompt
date: 2026-04-24
tags: [claude, prompt-caching, llm-agents, token-costs, mcp, telegram-bot]
type: success
status: n/a
reproducible: true
---

# Two cache_control segments so agent memory writes don't evict the whole Claude system prompt

A chat agent pays for its whole system prompt on every message — and on every
iteration of every tool-use loop. Anthropic's prompt cache cuts cached reads
to ~10% of the input price, but it works as a **prefix hash**: change one
byte, and everything from that byte to the end of the cached block is a miss.
That interacts badly with agent memory — the moment your agent learns
something new about the user, it rewrites its own prompt.

My Telegram coach bot is stateless: each message is a fresh Claude call with
instructions, the athlete's profile, zones, goal, long-term facts, and a set
of MCP tools; a tool-use loop re-sends all of it 3–5 times per answer.

First win was unrelated to caching: sending all ~55 tool schemas with every
"thanks!" was silly, so tools are filtered by message keywords into groups
(a core set always included) — about 75% fewer tokens on simple messages.

Then long-term memory arrived and broke caching. With a single cache marker
at the end of the system prompt, every `save_fact` call rewrote the facts
block, changed the prefix hash, and evicted **everything** — including the
instruction text that never changes.

The fix is embarrassingly small: two `cache_control: ephemeral` markers
instead of one. Segment one is the static instructions (~780 tokens,
byte-identical across users and days). Segment two is the per-user tail
(~240 tokens: date, profile, zones, goal, facts, language). A memory write
now invalidates only the tail; the static prefix stays hot. Anthropic allows
4 markers per request — we use 2.

The non-obvious part was what we had to *refuse* to build:

- **Top-N fact selection per message** (only inject facts relevant to the
  current question) — rejected. Any per-message selection makes the tail
  differ per message, so the tail cache never hits. Loading *all* facts every
  time is cheaper than loading fewer, differently each time.
- **Aggressive tool filtering** has the same tension: tools sit *above* the
  system prompt in the cached prefix, so a message that pulls in an extra
  tool group re-reads everything once. Liveable because the default group set
  covers most messages, and within one message's tool loop the list is
  constant — and the loop iterations are where the cache pays most.

Net effect: within the 5-minute TTL, loop iterations and follow-up messages
read the prompt at ~10% price, and frequent memory writes re-cache ~240
tokens instead of the ~1000+ of the whole prompt.

## Reproduce this

Prerequisites: an app calling the Claude API directly with the
[Anthropic SDK](https://docs.claude.com/en/api/client-sdks) and using
[prompt caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching);
a system prompt with a distinguishable invariant part (instructions) and a
volatile part (per-user / per-day data, agent memory). Works for any
provider with prefix-based caching — the marker syntax below is
Anthropic-specific.

Your agent will need from you: your current system-prompt assembly code, and
a list of which parts change per user, per day, or per memory write.

Steps:

1. Split `system` into an array of two text blocks, each with
   `cache_control: {"type": "ephemeral"}`: block one = instructions,
   guaranteed byte-stable (no interpolated dates, names, or counters);
   block two = everything volatile (date, profile, memory), ordered
   rarest-changing first for readability — after the marker it's one hash
   anyway.
2. Keep everything *above* the system prompt in the request — the tools
   array most of all — byte-stable across calls; if you must vary tools per
   message, make the default selection cover the common case, and never
   reorder or reword tool schemas casually.
3. Resist per-message personalization inside cached blocks (top-N memory
   selection, "relevant context only") — selection defeats the cache;
   include-everything usually costs less.
4. Read `usage` in every response: `cache_creation_input_tokens` and
   `cache_read_input_tokens` tell you exactly what happened.

Verify: send two messages within 5 minutes — the second must show
`cache_read_input_tokens` covering roughly the whole prompt. Then trigger a
memory write and send a third message: `cache_read` must still cover the
static block, and `cache_creation` must be roughly the size of your volatile
tail only. If a memory write causes `cache_creation` the size of the full
prompt, your static block isn't byte-stable — hunt the interpolated value.
