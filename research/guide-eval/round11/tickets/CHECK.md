# Ticket check (2026-11-09, before any run)

Each ticket was written by Codex (GPT-6-Sol, read-only) with `make_tickets.sh` from the story of the same name, then
checked by hand against the hidden answer key at the top of `graders/grade_<s>.py`. A ticket passes the check when every
fact the grader needs is in it and it adds nothing the story does not say.

| ticket | words (story) | facts the grader needs | in the ticket | added facts |
|---|---|---|---|---|
| s1 HR corridors | 437 (555) | `start`/`end` instead of `value`; units stay `%lthr` | yes, both, plus the corrected target object | none |
| s3 launchd | 366 (648) | `status` is read-only in zsh, use `rc=$?`; `USER` in the plist for "Not logged in" | yes, both | none |
| s7 Intervals OAuth | 375 (707) | each scope area once; no refresh_token or expiry; init as an authenticated POST returning the URL, then `window.location.assign` | yes, all three | none |
| s8 cache markers | 477 (731) | `system` as two blocks, static instructions first with `cache_control`, per-user tail after | yes | none |
| s10 keystroke trap | 367 (646) | once-only flag for text fields, `onChangeEnd` for sliders, `ScrollEndNotification` for scrolls | yes, all three, and the trap through helpers and listeners | none |
| s11 second write | 199 (343) | floats rejected by DynamoDB; store int percent or Decimal; seed one record before a write test | yes, all three | none |

What a ticket leaves out, by design: the story's "Reproduce this" contract (prerequisites, what the agent needs, step
lists, Verify) and the "Check if this applies" section. A fact found only in those parts and not an instruction stays,
said as something the colleague found (s10's trap through helpers and listeners came from the check section).

A first version (`../drafts/tickets-prose-v1/`) kept the whole story as prose, the contract included ("For the
reproduction, I used..."). It was dropped: it only tests headings against paragraphs, not the question this round asks.

## The three new stories (2026-11-09, before any round run)

Written the same way (`make_tickets.sh n4 n6 n10`, Codex GPT-6-Sol read-only) and checked the same way.

| ticket | words (story) | facts the grader needs | in the ticket | added facts |
|---|---|---|---|---|
| n4 Codex `-o` under a sandbox | 335 (580) | `-o` into the run folder fails under the profile and still exits 0; write to a scratch dir outside the denied paths and copy after `sandbox-exec` | yes, both, plus Vibe's `--output-dir` | none |
| n6 Hedera SDK | 215 (379) | `@hashgraph/sdk` 2.81.0 is frozen and not deprecated; install `@hiero-ledger/sdk`, one SDK only | yes, both, and that the API is unchanged | none |
| n10 Prisma 8 | 290 (448) | `@prisma/client@latest` is 7.10.1 while `prisma@latest` is 8; set up with `prisma orm init --yes`, client `@prisma/orm-postgres`, `contract emit`, `db init` | yes, all | none |

Checked by string search that the ticket's specific details (error texts, flags, dates, API calls) are in the story.

Reviewed by Valentina: pending. She started the round on 2026-11-09 before going to sleep ("do the whole testing with
open router models"), so the round ran on these tickets without her review.
