# Guide-eval round 8: the task in Russian, five samples per cell

Date: 2026-10-26. Written before any run.

Question (Valentina's): if a developer sets the task in their own language (Russian) instead of English, does a worklore story help more than it does with an English task? Two sub-questions, because they lead to different product decisions:

1. Task language. Does a Russian prompt lower the no-guide baseline? If it does, every story is worth more to a Russian-speaking developer.
2. Story language. Under a Russian task, does a Russian translation of the story help more than the English original? If not, worklore does not need localized stories.

The harness runs offline (no MCP, no web), so "searching the English solution" means recalling it; a drop in Russian is a recall effect, not a search effect.

## Design

Five arms, one difference of differences: (story gain in Russian) minus (story gain in English).

| Arm | Task | Note prefix | Story |
|---|---|---|---|
| none-en | English | | |
| example-en | English | English | English |
| none-ru | Russian | | |
| example-ru | Russian | Russian | English |
| example-ruru | Russian | Russian | Russian |

none-en and example-en are reruns of round 5 / round 7 cells so the English baseline is measured on the same day as the Russian one. The notes arm and the "follow" wording are out (both answered in rounds 5 and 7).

Six stories: four where the guide mattered in rounds 5 and 7 (s1 HR corridors 3/8 → 16/16, s3 launchd 2/9 → 17/18, s7 Intervals OAuth 3/7 → 12/14, s10 keystroke trap 4/7 → 12/14) and two where it did not (s8 cache markers 6/7 → 14/14, s11 second write 7/7 → 14/14) as controls. Same fixtures and graders as before, copied into this folder; the graders that require a cause to be named in ANSWER.md (s1, s3, s11) accept the Russian wording as well. The s7 "cause named" scan is recorded, not required, and also accepts Russian.

Translations: tasks, the note prefix, the ground-rules suffix and the six stories were translated by Claude (Fable 5.1) and reviewed by Valentina. Code identifiers, paths, error strings and scope strings stay in English because the fixtures and graders match them literally.

Seven agent configurations as in round 7: Claude Code with Opus, Sonnet and Haiku 5.5; Codex CLI with GPT-6-Sol at medium and low; Antigravity with Gemini 3.8 Flash and GPT-OSS 120B. The two Gemini 4 Argon configurations are out (Google AI Pro quota, assumed exhausted).

Five repetitions per cell, repetitions in the outer loop of each lane. 6 × 5 × 7 × 5 = 1050 runs. A run that dies on a usage limit is deleted and redone on a later pass.

Extra measurements, free: the language the agent writes ANSWER.md in; wall time per arm.

## Predictions, so the result can contradict them

- Opus, Sonnet and GPT-6-Sol (both efforts): no drop from none-en to none-ru on any story.
- Haiku, Gemini Flash, GPT-OSS: a drop on the two "fact" stories (s1, s7), none on the controls.
- The English story under a Russian task (example-ru) helps as much as under an English task (example-en): the difference of differences is within noise.
- The translated story (example-ruru) adds nothing over the English one; if anything it is slightly worse where the story quotes key names and the translation surrounds them with Cyrillic.
- With 35 runs per story and arm, round 7's "3/7 without" on s7 will be confirmed in the 10 to 20 of 35 range rather than being noise.
- Answer language: Claude and Codex answer in Russian when asked in Russian; GPT-OSS often answers in English.
