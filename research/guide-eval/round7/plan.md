# Guide-eval round 7: a second story for each kind

Date: 2026-10-20. Written before any run.

Round 5 tested six kinds of guide with one story each. One story per kind cannot separate "this kind of guide helps" from "this one story was written well or badly". Round 7 repeats the design with a second story per kind, same arms (none, follow, example, notes), same harness, one sample per cell. The two Gemini 4 Argon configurations are out (Google AI Pro quota exhausted until about 2026-10-25), so seven agent configurations: Claude Code with Opus, Sonnet and Haiku 5.5; Codex CLI with GPT-6-Sol at medium and low; Antigravity with Gemini 3.8 Flash and GPT-OSS 120B. 6 × 7 × 4 = 168 runs.

| # | Story | Kind (round 5 pair) | Fixture | Task | PASS |
|---|---|---|---|---|---|
| s7 | Intervals.icu OAuth quirks (radikkhaziev) | a fact on no web page (s1 HR corridors) | a coaching backend whose Intervals integration requests a scope area twice, expects refresh_token/expires_in and expires connections on a timer, and starts auth from a GET link; logs show symptoms only | "Athletes can't connect their Intervals.icu account ... Fix the integration" | scope areas once, no refresh/expiry assumption, init not a bare GET |
| s8 | Two cache_control segments (radikkhaziev) | a fact from the docs (s2 PostHogWidget) | a coach bot with one cache marker on a single system block that a memory write rewrites; usage log shows cache reads dropping to 0 after each save_fact | "every save_fact makes the next call pay full price ... Fix the caching" | static block with its own marker, independent of facts, before the tail; ≤ 4 markers |
| s9 | DynamoDB reserved words (Yahhi) | two bugs, one loud, one silent (s3 launchd) | a story API where `hidden` is bare in an UpdateExpression (crash) and in a ProjectionExpression (silently absent, so the feed filter never sees it); a fake table reproduces both behaviours | "Hiding a story crashes on prod, and a hidden story still shows in the feed ... fix it so it can't come back" | both causes named, hide works, hidden story absent from the feed |
| s10 | PostHog event per keystroke (Yahhi) | a trap to fall into (s4 Cache-Control) | a Flutter registration screen and an offers list with an events spec; the obvious wiring is onChanged | "Implement the analytics events in docs/EVENTS.md" | all six events wired and no capture fires per keystroke, per slider step or per scroll update |
| s11 | Crash on the second write (Yahhi) | a cause the evidence gives away (s5 soft 404) | a publish handler storing float similarity scores; the error log says "Float types are not supported" | "Publishing works once; the second publish returns 500 ... fix it so it can't come back" | cause named, a second publish succeeds under a fake table |
| s12 | Two-account authorization test (Yahhi) | a method (s6 MCP checkup) | a to-do API where like and view skip the visibility check on private tasks | "check this API's authorization ... fix what you find" | both gaps closed in a live probe, both named, no regression on public interactions |

Predictions, so the result can contradict them:
- s7 repeats s1 only partly: the symptom log reveals two of the three quirks (no refresh_token in the token response; the 401 on the GET link), so most agents fix those without the story; the scope rule ("each area once, :WRITE implies :READ") is the part the story carries. Expect none < with on the scope check specifically.
- s8 repeats s2: every agent knows multiple cache breakpoints; the story changes nothing.
- s9 repeats s3 if agents fix the loud crash and miss the silent projection; the story's blanket aliasing rule is what they lack. Expect none ≈ 3 to 5 of 7, with ≈ 7 of 7.
- s10 is the real second trap test: unlike s4, the naive implementation is the natural one. Expect several none runs to wire onChanged directly; with the story, 0 trap hits.
- s11 repeats s5: 7 of 7 without; the story adds the seeded test.
- s12 repeats s6: most agents find the two gaps by probing; the ones that only read the code may miss that like and view mutate; "follow" vs "example" shows whether a checklist helps on a method again.
- Wording: "example" ≥ "follow" overall, as in round 5. Notes arm: agents open the note when the task is hard (s7, s9), less when it is easy (s8, s11).
