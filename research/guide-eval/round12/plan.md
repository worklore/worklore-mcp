# Guide-eval round 12: updating a library, with the task in four languages

Date: 2026-11-15. Written before any run. Valentina approved it on 2026-11-15 ("let the Kùzu story be the last"): T1 and T2 run overnight, T3 waits for her review of their results.

## Why

Round 8 (Habr: https://habr.com/ru/articles/1106298/) found that with the task in Russian, some agents searched less and passed less. The comments asked three things this round answers:

- Is it Russian, or any language that is not English? Zippy: "try Ukrainian"; Trab_l13: Russian, Ukrainian, Belarusian, Armenian, Kazakh, Uzbek; Valentina's reply: add a couple of control languages. This round adds Ukrainian and Spanish as controls. Spanish is a large language with no sanctions in play, so a gap there is not about Russia.
- Does a standing line in AGENTS.md help instead of a note? dafremsky and buggzy2: "search first"; Slav2, ZamirHa and kuza2000: translate the task to English first. Here the line is the short brief from the library-updates research (see below), which includes "search for the upgrade guide".
- Other models. SabMakc: add DeepSeek V4.1 Flash and GLM 5.3 Flash, run inside Claude Code so that only the model changes. dkir70: results depend on agent + model, not the model alone. artalex: state the effort of every config. piton-vas: count tokens per task.

The task type changes from round 8: instead of forum fixes, a library update where agents are known to go wrong. Source: the update screens of 2026-11-01..08 (59 runs, worklore-research/findings/how-agents-learn-about-updates.md). Agents choose the version on npm before reading any docs, `npm view <pkg> version` hides deprecations, and docs inside the package get read while docs sites mostly don't. The docs-channels runs of 2026-11-14/15 found that a few lines in AGENTS.md changed results more than a docs MCP, a skill or llms.txt. That brief is the arm here, and it is what readyforagents.tech now measures for library teams.

## Tasks (2, with a third optional)

As built (2026-11-15): `fixtures/h` is round 11's n6 project with a working `src/transfer.ts` on `@hashgraph/sdk` pinned to 2.70.0; `fixtures/p` is round 11's working Prisma 7 control pinned to 7.6.0 (prisma, @prisma/client, @prisma/adapter-pg), and each run's database is a copy of `p_template`, which has the 7.6.0 migrations applied. Graders are round 11's `grade_n6.py` and `grade_n10.py` unchanged (`graders/grade_h.py`, `grade_p.py`). Controls (`controls/check.sh`): unmodified fixture FAIL on both; the fixture installed as is WORKS_ON_OLD_SDK / WORKS_ON_PRISMA7; round 11's references PASS. Round 11 baseline on the "add" versions of these tasks (EN, no story, 5 runs): Haiku 0/5 and 0/5, Codex low 0/5 and 1/5; with the story 5/5 everywhere.

Each task is rewritten from a screen as an update of an existing small project, so the prompt says "update", not "add":

| Task | Fixture | Where agents go wrong (screen) | Story (the S arm) | Visibility |
|---|---|---|---|---|
| T1 Hedera | a project on `@hashgraph/sdk` 2.x with a working `src/transfer.ts`; "update the Hedera SDK to the current supported version, keep transfer.ts working" | 0 of 6 found `@hiero-ledger/sdk`: npm shows `@hashgraph/sdk` as latest, not deprecated (2026-11-02-hedera-screen) | 2026-11-02-supported-hedera-javascript-sdk-has-a-new-name-in-npm | private |
| T2 Prisma | a project on Prisma 7 with the users/posts schema and script.ts, local PostgreSQL; "upgrade Prisma to the current version" | 3 of 6 stayed on 7: `@prisma/client@latest` is 7 next to an 8 CLI (2026-11-01-prisma8-screen) | 2026-11-01-current-prisma-from-npm-is-prisma-8-but-prisma-client-latest | private |
| T3 Kùzu (optional) | a Python project on kuzu 0.11 with a database file; "move to LadybugDB" | 2 of 6 installed the old `real_ladybug`, 3 of 6 lost the original data (2026-11-08-kuzu-to-ladybug) | 2026-11-08-migrating-from-k-zu-to-ladybugdb-old-database-files-won-t-op | PUBLIC |

T3 risk: the story is public. On 2026-11-15 Search Console says "Discovered, currently not indexed", but indexing just doubled (126 pages) and Bing gets every deploy through IndexNow. In round 8, published stories reached the "no story" runs through Google. Use T3 only if Valentina hides the story for the duration of the round. Otherwise run T1 and T2 only.

Graders: reuse each screen's hidden `grade.py`, with PASS meaning the update actually landed: `@hiero-ledger/sdk` imported and both hidden inputs verify; Prisma 8 installed, script prints users with posts; the LadybugDB file opens and the original is kept. Controls: the reference passes, the untouched fixture fails, and an "updated on the old package" version gets its own grade (WORKS_ON_OLD).

## Languages (4)

EN, RU (round 8 link), UK, ES. Valentina has no Ukrainian reader, so (her call) ChatGPT translated the task texts into all three languages (Codex, GPT-6) and Gemini 3.8 Flash and ChatGPT reviewed them; Gemini 4 Argon's quota was out until 2026-11-21. Fixes both reviewers agreed on were applied (`translate/`). The Russian ground rules and note prefix are round 8's, reviewed by Valentina, unchanged. The story stays in English in every language, as round 8's example-ru. Code, package names, paths and errors stay in English. Optional fifth language, if a reader offers to check it: Kazakh or Belarusian.

## Arms (3)

| Arm | What is in the workdir before the agent starts |
|---|---|
| N none | nothing (web on, as in the screens) |
| L line | 4 lines in AGENTS.md and CLAUDE.md, in English, in all four languages: (1) before you pick a package or version, run the full `npm view <pkg>` and read `deprecated` and the dist-tags, not just `version`; (2) check whether the package moved to a new name; (3) read the docs that ship in the package (AGENTS.md, README, type files) before the website; (4) search the web for the official upgrade guide before changing code. No library is named. |
| S story | the private worklore story as a note, as in rounds 5 to 8 (the note in the task's language, the story in English) |

The line is in English in every language arm, because people keep AGENTS.md in English even when they chat in another language (kryvichh). One extra cell, if the budget allows: RU + the line translated into Russian.

The "translate the task to English first" rule is not a separate arm in this round. It goes in the next one, together with local models.

## Agents and models (4 configs, effort stated)

| Config | Why |
|---|---|
| Codex CLI, GPT-6-Sol, effort low (as rounds 8 and 11) | searched 0 of 10 with the RU task in round 8 |
| Kimi Code, K3.1, default effort | 0 of 10; macOS sandbox (output goes to Moonshot) |
| Claude Code, Haiku 5.5, default effort | searched 6 of 10: the contrast |
| Claude Code + DeepSeek V4.1 Flash (Anthropic-compatible endpoint) | SabMakc: the same agent, a different model, which answers dkir70. `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`, model `deepseek-flash`. Smoke 2026-11-15: npm task and WebSearch both work through it; $10 balance, key in `~/.zshenv` (guarded). GLM 5.3 Flash is the fallback |

## Size

Arms N and L in all 4 languages and S in EN and RU, 5 repetitions per cell: per task and config 4×5 + 4×5 + 2×5 = 50 runs. T1 + T2: 50 × 2 × 4 = **400 runs**; T3 adds 200. Eight lanes (agent × task) run in parallel, repetitions in the outer loop. Codex, Kimi and Haiku run on subscriptions; DeepSeek on its API key, roughly $0.05-0.2 per run (to be measured on the pilot).

## Before the full round

1. Build both update fixtures and check the controls.
2. Pilot: EN and RU, arm N, 2 runs per config. The task stays only if the baseline leaves room to improve (under about 70%).
3. Check that the two private stories still answer "missing" without a token, and look for both titles on Google and Bing.

## Measurements

- PASS / WORKS_ON_OLD / FAIL from the hidden grader.
- Searched: counted from real tool calls, not the `web_used` field (wrong for Claude in round 8).
- Read `deprecated`: full `npm view` or install warning seen and acted on (sources.py from the findings).
- Opened the AGENTS.md line or the note.
- Language of ANSWER.md.
- Exposure: any request to worklore.dev, or a search result pointing to it.
- Time, tokens in and out (piton-vas), effort (artalex).

## Predictions, so the result can contradict them

- N: UK lands close to RU, and ES close to EN. If ES drops as much as RU, the gap is "not English", not Russian.
- L lifts Codex low and Kimi in every language, because it gives them a reason to run the full `npm view` and search; the language gap gets smaller under L.
- S beats L on T1 (the rename is a fact the line can lead to but does not state) and roughly matches it on T2.
- DeepSeek inside Claude Code searches about as often as Haiku (search is the agent's habit), but passes less.

## Article

Habr follow-up (RU), then dev.to (EN). The story arm is worklore. The line arm comes from the library-updates research and is what readyforagents.tech checks for library teams: one sentence in Methods, one at the end, no ad. The text never says it was written with AI (Habr rule 4).

## Change after the first night (2026-11-16)

T2 as written ("upgrade Prisma to the current version") turned out to measure something else under the line arm: `prisma@latest` is 8.0.0-rc.33, and agents that read the dist-tags as the brief asks chose the stable 7.10.1 on purpose ("every 8.x is an RC"). That is a defensible reading, and the grader counts it as FAIL. Valentina's call: rerun T2 with the target named, "upgrade Prisma to version 8" (task `p8`, same fixture, story, grader and arms, 200 runs). The `p` results stay in the table as the first version. T3 (Kùzu) is dropped: Hedera and Prisma are enough (her call, same day).
