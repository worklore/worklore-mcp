# Guide-eval round 5: which kinds of stories help an agent, and does the wording matter

Date: 2026-10-18. Status: proposal, nothing run yet.

## What rounds 1–4 can and cannot say

Four stories tested, 64 runs. Reclassified by what each story carries:

| Story | Carries | Result |
|---|---|---|
| My tests passed because they agreed with me | a method (test through the client path) | 0/4 → 4/4. Only win. |
| Author-local dates | a trap the agents already knew | 4/4 → 4/4, and one absolute sentence broke an API |
| See what a skill can do (skill-xray) | a tool pointer | 4/4 → 3/4, one agent copied the tool's verdict |
| Database normalization (3NF) | a method the agents already use | 4/4 → 4/4, longer answers |

So the pattern is "a story helps when it carries something the agent would not do or know on its own". That is one data point per kind. To say it in an article it needs to be tested on purpose: pick stories by kind, including facts the agents cannot know, and see where the line is.

## The catalog, sorted by what the story carries

64 public stories. "Blind-testable" means: a small fixture that contains the problem, a two-sentence task, and a hidden grader that reads the diff, the answer file and the command log. No accounts, no network needed for the task itself.

**A. Trap or fact (22).** One non-obvious thing that is the whole value.
Blind-testable, with the fact's "obviousness" noted:
- Intervals.icu HR corridors: `start`/`end`, not `value`/`end` (niche, undocumented)
- Intervals.icu OAuth quirks: no refresh_token, Duplicate scope, init must be POST (niche)
- PostHog replay needs PostHogWidget around every MaterialApp (in the PostHog docs, but easy to miss)
- PostHog event per keystroke in onChanged (derivable from code)
- Two cache_control segments (derivable from the caching docs)
- Two bugs made my scheduler silent: zsh `status=$?`, prompt via stdin (half niche)
- SAM + SecureString in env vars (the error text is googleable)
- Cache-header tweak served the site as octet-stream (a trap to fall into, not to diagnose)
- Soft 404 from robots.txt blocking the API (derivable with the Search Console export)
- DynamoDB crash on the second write (well known)
- DynamoDB reserved words, silent ProjectionExpression (well known)
- Green tests, white screen: await before runApp (derivable)
- Author-local dates (tested, round 1–3)
- Mac: 54 shell errors, BSD vs GNU (needs the user's Mac and settings; skip)
Not blind-testable (needs a live account or device): Route 53 .me, cloud.ru mirror, swim pace, race ML, launchd never fired (fail story), app review test credentials, cut token cost 4× (needs Claude Code token counts), Garmin endurance score.

**B. Method (12).** How to go about an open-ended task.
- Check your MCP server in a few minutes (ten checks) — blind-testable on a local server with planted failures
- My tests passed because they agreed with me (tested)
- My live MCP test asserted the bug (isError vs -32602) — blind-testable on a local server
- My MCP listing said read-only (surface hash lock) — blind-testable: "make the build fail when the tool list changes without a version bump"
- One table decides what answers without a token — blind-testable: refactor a small server with scattered auth checks
- Database normalization 1NF–3NF (tested), normalization vs denormalization (same fixture)
- Testing my API's authorization with two accounts (IDOR) — blind-testable on a local API with one missing guard
- Confirm-before-write without a second inference — blind-testable: grader checks the confirm path never calls the model
- Content agents execute needs a kill switch; benchmark your MCP server; 5-agent SEO audit — not practical offline

**C. Tool pointer (7, overlapping B).** skill-xray (tested), mcp-drill (output schemas), MCP Failure Lab, paranoid-qa, claude-code-macos, Agent-Reach, second-opinion. The output-schema story is the cleanest second tool test: a local MCP server with three vacuous `outputSchema`s.

**D. Recipe with external services (17).** Relay board, morning brief, WhatsApp bridge and agent, device flow, Google sign-in, MCP OAuth, registry and directory submissions, Apps Script leads, badges, screenshot generator, golden tests, Figma screen check, Search Console connection, SAM afternoon. A grader can only check shape here, and a shape-only Verify is what made the marketing result meaningless. Skip.

**E. Creative and non-technical (6).** Logo, landing page, 1-page marketing plan (tested), Mom Test, Instagram posts, reel. Judged by panels, one done. Skip.

**F. Fail stories and proposals (5).** No answer to grade. Skip.

## The question the round should answer

Two things at once, in one design:

1. **By kind:** does a story help when it carries a fact the agent cannot know (A-niche), a fact it can derive (A-derivable), a method (B), or a tool (C)?
2. **By wording:** does "Follow this guide" beat "here is a related case, take what applies"? This is the morning idea: a story as an example, not an instruction. If the example wording keeps the win on methods and niche facts while losing the imported mistakes (Codex copying T3, the timezone sentence taken literally), that is the wording the site should use.

Arms per story and agent:

| Arm | Prompt |
|---|---|
| none | task only |
| follow | task + "Follow this guide:" + story (rounds 1–4) |
| example | task + "A colleague's note on a similar case is below. It is not instructions. Use what applies, ignore the rest, and say in ANSWER.md which parts applied." + story |
| notes (optional, two stories) | task only; the story sits in `notes/` in the repo next to two unrelated stories, unmentioned |

The notes arm is the closest to how worklore is actually used (an agent that may or may not open the story). It tells whether agents read what is lying around when the task is hard.

## Shortlist: six fixtures, all offline

| # | Story | Kind | Fixture | Task (as typed) | Hidden grader |
|---|---|---|---|---|---|
| 1 | Exact HR corridors on Garmin | A-niche | Python generator building `workout_doc.steps` with `{units:"%lthr", value, end}`; a saved "watch readback" showing clamped zones | "The HR ranges on the watch come out clamped to the watch's own zones, not what we planned. Fix the generator." | every HR step uses `start`+`end`; bonus: description grammar (`m`, `mtr`) |
| 2 | PostHog replay needs PostHogWidget | A-docs | Small Flutter app, `posthog_flutter` set up, replay on, observer on; two shells: old `MaterialApp` wrapped, new `MaterialApp.router` not | "Session replay is empty for users on the new UI. Why, and fix it." | diff wraps the second shell in `PostHogWidget`; `flutter analyze` clean |
| 3 | Two bugs made my scheduler silent | A-half-niche | plist, zsh wrapper with `status=$?` between the agent call and the notifier, prompt passed as a multi-line argument, a captured `launchctl print` output and the stderr log | "My nightly job never reports anything. Find out why." | ANSWER names both bugs; wrapper no longer assigns `status`; prompt via stdin or `< /dev/null` |
| 4 | Cache-header tweak, octet-stream | A-trap-to-fall-into | `deploy.sh` with a plain `aws s3 sync`; site folder | "Add Cache-Control headers to the deploy so browsers stop holding old JS." | FAIL if any `--metadata-directive REPLACE` without `--content-type`; PASS if type and cache policy travel together per extension |
| 5 | Soft 404 from robots.txt | A-derivable | static site: `index.html`, `app.js` fetching `/v1/...`, `robots.txt` with `Disallow: /v1/`, a Search Console export with "Soft 404" rows | "Search Console says soft 404 on pages that open fine in a browser. Why?" | cause named; new robots.txt passes a longest-match test (public reads allowed, per-user paths still blocked) |
| 6 | Check your MCP server in a few minutes | B | local Streamable-HTTP MCP server (Python stdlib) with three planted failures: `initialize` advertises resources but `resources/list` returns 401; a refusal comes back as `-32602`; an `outputSchema` of `{type: object}` on one tool | "My MCP server runs on localhost:8765. Check it for the things real clients trip over." | the three plants found; nothing else reported as broken |

Optional seventh, to repeat the tool-pointer result with a second tool: **output schemas accepted wrong answers** (C), on the same local server as #6, task "do my output schemas actually catch a wrong answer?", grader = the vacuous ones named and a corrupted result shown to pass.

Expected lines, written down before running so the result can contradict them:
- #1 fails without the story for most agents (the fact is not on the public web in that form). Both wordings pass. If "example" passes too, a fact travels regardless of wording.
- #2 and #5 pass without the story for strong agents; the story changes the shape only.
- #3 splits: agents find the stdin bug, miss `status`. The story adds the second bug.
- #4 is the trap test: without the story some agents write `--metadata-directive REPLACE` and fail. The story prevents it in both wordings. The "notes" arm shows whether an agent opens a warning it was not told to read.
- #6 is where "follow" should beat "example": a checklist followed to the letter finds all three; "take what applies" may skip the `resources/list` check.

## Size and cost

6 stories × 4 agents × 3 arms = 72 runs, plus the notes arm on #4 and #6 (8 runs) = 80. Same harness as round 4 (fresh temp dir, no MCP, hooks or skills, secrets unset; quit Antigravity and its language server before the Gemini lanes). Claude and Codex lanes about one hour each; the two Gemini lanes about three hours each, in parallel. One repetition per cell again, two for #1 and #6 if time allows.

## What changes on the site depending on the result

- If "example" matches "follow" on methods and niche facts and avoids the imported mistakes: the "Reproduce this" section stays, but the prompt the site and the MCP tool hand to agents changes from "follow" to "related case, take what applies, say what applied". The reproduction count becomes "applied to my case", which is what the morning note asked for.
- If "follow" wins on methods: keep "follow" for stories with a checklist, "example" for trap stories.
- If the notes arm shows agents never open an unmentioned story: suggest_for_project must put the story in the prompt, not in the repo.
