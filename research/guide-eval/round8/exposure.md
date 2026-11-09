# No-story runs that saw the worklore story

Google indexed the two forum-fact stories on 2026-10-21 (s7) and 2026-10-24 (s1), first impressions in Search
Console; round 8 ran from 2026-10-26, so an agent without the story could find it on the web. A run counts as
exposed when its log shows the story page fetched, a story URL in search results, or, for Antigravity, worklore.dev
among the sources of a search summary (Google grounding; those summaries are kept only in Antigravity's local
conversation store, ~/.gemini/antigravity-cli/conversations, which this script reads when it is there).
Limits: Codex's built-in web search logs the query but not its results, so for Codex this is a lower bound.
Two Antigravity runs (r1) have no stored conversation; they searched site:worklore.dev and are counted as exposed.
Claude's search results are logged with their links and never included worklore.dev.

| run | passed | how |
|---|---|---|
| s1-agy-flash-low-none-en-r1 | yes | searched site:worklore.dev (no stored conversation) |
| s1-agy-flash-low-none-en-r2 | yes | in Google grounding sources |
| s1-agy-flash-low-none-en-r3 | yes | in Google grounding sources |
| s1-agy-flash-low-none-en-r4 | yes | in Google grounding sources |
| s1-agy-flash-low-none-en-r5 | yes | in Google grounding sources |
| s1-agy-flash-low-none-ru-r1 | yes | searched site:worklore.dev (no stored conversation) |
| s1-agy-flash-low-none-ru-r2 | yes | in Google grounding sources |
| s1-agy-flash-low-none-ru-r3 | yes | in Google grounding sources |
| s1-agy-flash-low-none-ru-r4 | yes | in Google grounding sources |
| s1-agy-flash-low-none-ru-r5 | yes | in Google grounding sources |
| s1-agy-oss-none-en-r2 | yes | in Google grounding sources |
| s1-codex-sol-none-en-r2 | yes | in search results |
| s1-kimi-k28-none-en-r2 | yes | page fetched, in search results |
| s1-kimi-k28-none-en-r3 | yes | page fetched, in search results |
| s1-kimi-k28-none-en-r4 | yes | page fetched, in search results |
| s1-kimi-k28-none-en-r5 | yes | page fetched, in search results |
| s1-kimi-k28-none-ru-r3 | yes | page fetched, in search results |
| s1-kimi-k28-none-ru-r5 | yes | page fetched, in search results |
| s1-kimi-k31-none-en-r4 | yes | page fetched, in search results |
| s1-kimi-k31-none-en-r5 | yes | page fetched, in search results |
| s7-agy-flash-low-none-en-r2 | yes | page fetched, in Google grounding sources |
| s7-agy-flash-low-none-en-r3 | no | in Google grounding sources |
| s7-agy-flash-low-none-en-r4 | no | in Google grounding sources |
| s7-agy-flash-low-none-en-r5 | yes | page fetched, in Google grounding sources |
| s7-agy-flash-low-none-ru-r2 | no | in Google grounding sources |
| s7-agy-flash-low-none-ru-r3 | no | in Google grounding sources |
| s7-agy-flash-low-none-ru-r4 | no | in Google grounding sources |
| s7-agy-flash-low-none-ru-r5 | no | in Google grounding sources |
| s7-codex-sol-none-en-r3 | yes | in search results |
| s7-codex-sol-none-en-r4 | yes | in search results |
| fresh/s1-codex-sol-fresh-en-r3 | yes | in search results |
| fresh/s1-codex-sol-low-fresh-en-r2 | yes | in search results |
| fresh/s1-codex-sol-low-fresh-en-r4 | yes | in search results |

## Pass rates without a story, all runs and without the exposed ones (round 8 runs only)

| agents | arm | all runs | exposed | without exposed |
|---|---|---|---|---|
| seven | none-en | 132/210 (62.9%) | 13 | 121/197 (61.4%) |
| seven | none-ru | 118/210 (56.2%) | 9 | 113/201 (56.2%) |
| Kimi | none-en | 37/60 (61.7%) | 6 | 31/54 (57.4%) |
| Kimi | none-ru | 29/60 (48.3%) | 2 | 27/58 (46.6%) |
| nine | none-en | 169/270 (62.6%) | 19 | 152/251 (60.6%) |
| nine | none-ru | 147/270 (54.4%) | 11 | 140/259 (54.1%) |

## Per agent, the two stories where it happened

| agent | story | none-en | without exposed | none-ru | without exposed |
|---|---|---|---|---|---|
| claude-opus | s1 | 4/5 | 4/5 | 5/5 | 5/5 |
| claude-opus | s7 | 3/5 | 3/5 | 3/5 | 3/5 |
| claude-sonnet | s1 | 4/5 | 4/5 | 3/5 | 3/5 |
| claude-sonnet | s7 | 2/5 | 2/5 | 4/5 | 4/5 |
| claude-haiku | s1 | 3/5 | 3/5 | 2/5 | 2/5 |
| claude-haiku | s7 | 1/5 | 1/5 | 2/5 | 2/5 |
| codex-sol | s1 | 3/5 | 2/4 | 0/5 | 0/5 |
| codex-sol | s7 | 5/5 | 3/3 | 3/5 | 3/5 |
| codex-sol-low | s1 | 5/5 | 5/5 | 0/5 | 0/5 |
| codex-sol-low | s7 | 3/5 | 3/5 | 1/5 | 1/5 |
| agy-flash-low | s1 | 5/5 | 0/0 | 5/5 | 0/0 |
| agy-flash-low | s7 | 2/5 | 0/1 | 1/5 | 1/1 |
| agy-oss | s1 | 1/5 | 0/4 | 0/5 | 0/5 |
| agy-oss | s7 | 0/5 | 0/5 | 0/5 | 0/5 |
| kimi-k28 | s1 | 4/5 | 0/1 | 2/5 | 0/3 |
| kimi-k28 | s7 | 1/5 | 1/5 | 2/5 | 2/5 |
| kimi-k31 | s1 | 3/5 | 1/3 | 2/5 | 2/5 |
| kimi-k31 | s7 | 5/5 | 5/5 | 0/5 | 0/5 |
