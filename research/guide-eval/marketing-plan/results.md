# Cross-agent experiment, non-technical story: the 1-Page Marketing Plan skill

Date: 2026-10-03. This extends the technical experiment in `../results.md`.
Setup: one story, 4 agents, 2 arms, so 8 runs. All 8 exited 0. None hit the 15-minute timeout, and none failed on auth or quota. Wall times were 63 to 210 s.

Story: `2026-09-01-the-1-page-marketing-plan-as-an-agent-skill-interview-me-bui` ([worklore.dev](https://worklore.dev/s/2026-09-01-the-1-page-marketing-plan-as-an-agent-skill-interview-me-bui.md)).
Its skill exists at `worklore/worklore-skills/skills/one-page-marketing-plan-sheet/SKILL.md`, which I checked and fetched on 2026-10-03.

## Method
- **Client:** a fictional one-person ceramics studio, Taller Lento in Chacarita, Buenos Aires, run by Lucía (`client_brief.md`).
  - Facts given: mugs at ARS 28,000; a monthly wheel class with 6 seats at ARS 120,000; a taster class at ARS 40,000; a Sunday Palermo fair; Instagram with 1,900 followers; bookings on WhatsApp.
  - Constraints: 5 h a week, about US$50 a month, Spanish and English audience.
  - The brief is framed as "answers to the questions you would ask me, don't wait for me". It describes "the sale" in her own words ("it worked = a stranger booking a class … and then staying"), not as a label.
  - The same brief was used in every run.
- **Prompts:** both arms start with "Make me a 1-page marketing plan for my business. My answers … are in client_brief.md".
  - WITH also gets "Follow this guide:" followed by the story's raw markdown.
  - Both arms get the same neutral notes:
    - there is no Google Sheets access;
    - save `plan.csv` (a 3×3 grid importable into Sheets) and `plan.md`;
    - keep anything downloaded inside this folder;
    - don't publish or report anything.
  - Nothing discourages fetching the SKILL.md (`prompts/`).
- **Isolation (lessons from the last run):**
  - Each run had a fresh `mktemp -d /tmp/mp-XXXXXX` workdir with no "worklore" or "eval" in the path.
  - Outputs were moved to the scratchpad and the workdir was deleted as soon as each run ended. Graders, the answer key and the rubric never sat in a workdir.
  - Claude ran with an empty strict MCP config, slash commands and skills disabled, user settings off and hooks off. This is the same as last time, and it means the installed `one-page-marketing-plan-sheet` skill could not load.
  - WORKLORE_TOKEN, WORKLORE_API and GEMINI_API_KEY were unset for every agent.
- **Agents:**
  - claude = Claude Code 2.1.285 with `claude-opus-5-5`
  - codex = Codex 0.160.0 with `gpt-6-sol` at medium reasoning
  - agy-pro = Antigravity 1.2.16 with `gemini-3.1-pro-high`
  - agy-flash = Antigravity 1.2.16 with `gemini-3.8-flash-high`
- **Grading A (scripted, `graders/grade_format.py`):** the story's Verify, adapted to CSV, checked in plan.csv:
  - a title "1-Page Marketing Plan — <business>" (any dash, any case; whether the exact form appears is recorded separately);
  - "the item" and "the sale" stated above the grid;
  - Before, During and After phases;
  - all nine Dib squares named and non-empty. Abbreviations and synonyms such as "LTV" and "lead capture system" are accepted. Renamed squares are not.
  - plan.md must also exist.
- **Grading B (blind judging):**
  - The 8 plan.md files were shuffled with a seeded RNG (key in `judging/key.json`). Model and vendor names, "worklore" and "SKILL.md" were redacted; only one token occurred, in one plan.
  - Every judge saw the brief, the fixed rubric (`judging/rubric.md`) and all 8 plans in one prompt. Each criterion was scored 1–5 with a one-sentence reason, plus an overall score of 1–10, returned as JSON.
  - Judges:
    - `second-opinion -w codex` (GPT-6)
    - `-w gemini-pro` (Gemini 3.1 Pro)
    - `-w gemini-flash` (Gemini 3.8 Flash)
    - `claude -p --model sonnet` with no tools
  - I unblinded only after all four had returned.

## Results

| agent | arm | format (Verify) | title | item | sale | phases | 9 squares | C1 specific | C2 sale | C3 plain | C4 doable | C5 consistent | overall (mean of 4) | codex | gemini-pro | gemini-flash | claude-sonnet | time |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude | without | fail | n | n | n | Y | n | 5.00 | 5.00 | 4.75 | 4.25 | 4.75 | **9.00** | 8 | 9 | 10 | 9 | 74s |
| claude | with | **PASS** | Y | Y | Y | Y | Y | 5.00 | 5.00 | 5.00 | 4.25 | 4.25 | **9.00** | 8 | 10 | 9 | 9 | 134s |
| codex | without | fail | n | n | n | n | n | 4.50 | 5.00 | 4.25 | 4.75 | 4.75 | **7.50** | 9 | 6 | 8 | 7 | 121s |
| codex | with | fail | n | n | n | Y | n | 4.00 | 4.75 | 4.75 | 4.50 | 4.50 | **7.50** | 9 | 7 | 8 | 6 | 123s |
| agy-pro | without | fail | n | n | n | n | Y | 3.50 | 4.00 | 3.50 | 3.50 | 3.50 | **6.25** | 7 | 6 | 6 | 6 | 63s |
| agy-pro | with | **PASS** | Y | Y | Y | Y | Y | 2.75 | 4.50 | 4.25 | 3.00 | 4.00 | **5.00** | 7 | 5 | 4 | 4 | 71s |
| agy-flash | without | fail | n | n | n | Y | Y | 5.00 | 5.00 | 3.50 | 3.50 | 3.75 | **7.50** | 6 | 8 | 10 | 6 | 210s |
| agy-flash | with | **PASS** | Y | Y | Y | Y | Y | 4.50 | 4.75 | 2.25 | 3.00 | 3.75 | **5.75** | 6 | 6 | 6 | 5 | 94s |
| **all** | without | 0/4 | | | | | | 4.50 | 4.75 | 4.00 | 4.00 | 4.19 | **7.56** | | | | | |
| **all** | with | 3/4 | | | | | | 4.06 | 4.75 | 4.06 | 3.69 | 4.12 | **6.81** | | | | | |

Overall scores with same-vendor judges removed (a Claude plan scored only by codex, gemini-pro and gemini-flash, and so on):

| agent | without | with |
|---|---|---|
| claude | 9.0 | 9.0 |
| codex | 7.0 | 7.0 |
| agy-pro | 6.5 | 5.5 |
| agy-flash | 6.0 | 5.5 |
| mean | 7.1 | 6.75 |

The ranking does not change.

## Analysis

**The story nails the format and does nothing for quality.**
- Format: 3 of 4 WITH runs pass the story's Verify; 0 of 4 WITHOUT runs do.
- Quality: the blind judges scored WITH no better on average (6.8 vs 7.6 overall; 6.75 vs 7.1 without same-vendor judges).
- By agent: Claude tied at 9.0. Codex tied at 7.5. Both Gemini agents got *worse* with the guide: agy-pro 6.25 to 5.0, agy-flash 7.5 to 5.75.
- With one sample per cell, read this as "no evidence the story improves the plan itself", not "the story hurts".

**What the story actually changed:**
- **The two assumptions moved to the top.** Every WITH plan.md opens with *the item* and *the sale* before the grid, and three CSVs carry them as rows 2–3. No WITHOUT plan used that structure.
- **The sale was already right without the story.** All 8 plans, in both arms, put class bookings and retention first (C2 is 4.0–5.0 everywhere). The brief all but says it ("a tourist buying one mug … doesn't change my month"), so this test cannot show whether "define the sale first" helps when the sale is ambiguous, as in the story's own art-project example.
- **Dib's exact nine squares and the band layout.** Claude, agy-pro and agy-flash produced the SKILL.md's layout: title row, two assumption rows, a band row per phase, then one row of three squares. agy-flash even downloaded the story's example Sheet as CSV to copy it.
- **Plain language per square.**
  - Claude WITH added an "In plain words: …" line under each square. It got the highest plainness score (C3 5.0).
  - agy-pro WITH became much plainer (3.5 to 4.25) but also much thinner: 381 words, and no prices, budget or schedule (C1 2.75, C4 3.0). Two judges called it "too generic".
  - agy-flash WITH kept marketing jargon ("unit economics", "cohorts", "top of funnel") next to the plain-language notes and scored lowest on C3 (2.25).
- **Squares:** I did not score squares one by one. In the judges' reasons, the WITH gains are in the framing (assumptions, square explanations). The WITH losses are in C1 (specific) and C4 (doable), mainly in the agy plans. The renewal and referral squares (LTV, Referrals) looked the same in both arms: everyone proposed a week-3 renewal ask and bring-a-friend.

**Did agents follow "draft-first / define the sale first"?** Headless, nobody could interview the client, so "draft-first" could only show up as framing.
- Claude WITH framed the plan as a draft ("This draft comes from your brief … every guess is listed under Assumptions I made") and listed its assumptions.
- Codex WITH said it would "pin down what counts as a conversion, then draft the nine squares", and did.
- agy-flash WITH quoted the story ("Define the sale before anything else").
- agy-pro WITH stated the item and the sale at the top with no comment.
- So all four WITH runs defined the sale first, explicitly. Interestingly, Claude WITHOUT also ended with "My assumptions (please correct me)".

**Fetching the SKILL.md:**
- Claude WITH git-cloned the repo, read SKILL.md, then deleted the clone.
- agy-pro WITH cloned it into the workdir.
- agy-flash WITH curled the raw SKILL.md, plus the example Sheet's CSV export.
- Codex WITH never fetched it. It read two *locally installed* marketing skills from `~/.agents/skills` instead (`product-marketing-context`, `marketing-ideas`), and Codex WITHOUT read `marketing-ideas` too. This is why Codex WITH renamed the squares to plain phrases ("Who", "What to say", "Where to show up", "Get a contact" …) and failed the Verify on title, assumptions in the CSV, and square names. Its plan.md does have the right title and the sale.

**Arms where WITHOUT did as well or better:**
- **Claude WITHOUT (9.0)** equals Claude WITH. It is the most compact strong plan (1,023 words): a transposed 3×3 (phases as columns), plain names per square, a peso budget split, a 5-hour split, monthly metrics, and a "say no to" list. It fails the Verify only because it uses its own square names and no title or assumption rows.
- **Codex WITHOUT (7.5)** equals Codex WITH, and it did not use Dib's framework at all. Its own 3×3 is Goal, Customer, Offer / Fair to chat, Instagram + Maps, Book + follow up / Keep + refer, Weekly routine, Money + scorecard. For a non-marketer that is arguably *more* useful, because it budgets time and money in the grid itself.
- **agy-flash WITHOUT (7.5)** wrote the whole plan in Spanish (4,000 words), with Spanish/English scripts. Two judges loved it (8 and 10) and two found it long and jargon-heavy (6 and 6).

## Judges: agreement and bias
- **Agreement:** Spearman correlation of the overall score across the 8 plans:

  | | gemini-pro | gemini-flash | claude-sonnet |
  |---|---|---|---|
  | codex | 0.20 | 0.17 | 0.55 |
  | gemini-pro | | 0.88 | 0.79 |
  | gemini-flash | | | 0.76 |

  The two Gemini judges and Sonnet agree well. Codex is the outlier.
- **Codex judge self-preference.** It gave both Codex plans 9/10, while the other three judges averaged 7.0 for each. On non-Codex plans it was in line with the rest (7.0 vs 7.1). That is a +2 own-plan bias, and it explains most of its low agreement.
- **Gemini 3.8 Flash judge self-preference, on one plan.** It gave the agy-flash WITHOUT plan 10, against 6.7 from the others. On agy-flash WITH it was in line (6 vs 5.7).
  - The Gemini judges as a vendor showed little bias on the four Google plans (gemini-pro +0.5, gemini-flash −0.2, net of how they scored other plans).
  - Gemini 3.1 Pro showed none on agy-pro's plans.
- **Sonnet judge.** It gave Claude plans the same 9 the other judges did. It was the harshest on everything else: 5.7 vs 6.9 for the other judges on non-Claude plans. That looks like strictness, not inflation; the net self-preference statistic is +1.2 because of it.
- **Robustness:** removing same-vendor judges leaves the ranking unchanged. Claude ≫ Codex > agy, and WITH ≤ WITHOUT.

## Surprises
1. **The story made the Gemini plans worse.** agy-pro WITH reduced the plan to a 381-word framework-filling exercise. agy-flash WITH copied the example Sheet's structure but wrote in consultant-speak. The framework seems to pull these agents toward "fill the nine boxes" and away from "solve Lucía's problem". Claude kept the substance and added the frame.
2. **agy-flash WITH downloaded the story's example Google Sheet** (`/export?format=csv`) to mirror its layout. That is resourceful, and also a reminder that a public example link in a story is something agents will consume.
3. **agy-flash WITHOUT ran six web searches** for Dib's template and square names (12 log lines; each query appears twice). It did not search for anything experiment-related: no path leak this time.
4. **Codex used locally installed marketing skills (`~/.agents/skills`) in both arms.** This is a leak of general marketing guidance, the same in both arms, and it is not the story's skill.
5. **Small stray writes:**
   - Claude WITH wrote a helper to `/tmp/gen_plan.py`, outside its workdir. I moved it to `runs/claude-with/stray-tmp-gen_plan.py`.
   - agy-pro WITH left a full `git clone` of worklore-skills in its workdir. It is not copied into the repo.
   - Claude wrote its usual session state under `~/.claude/projects/-private-tmp-mp-*`.
   - Nothing under ~/projects was touched by agents (checked against the command logs). Skill directories are unchanged (listing diff before and after).
6. Nobody fabricated a Google Sheet link. Everyone delivered CSV and MD, as told.

## Suggested story edits
- **Add "what the plan must contain beyond the grid".** The best plans in both arms (Claude ×2, Codex WITHOUT) all added a weekly time split, a budget split and 3–4 monthly numbers to check. The skill asks for none of these, and the frame-following agy plans left them out and lost points on "doable". Suggest a 10th "Constraints" row under the grid: hours per week, budget, and the one metric for the sale.
- **Plain language means explaining the box, not renaming it, and no jargon in the answers either.** Codex WITH replaced Dib's names with plain phrases, which breaks the Verify. agy-flash WITH explained the boxes but filled them with jargon. Say: "keep Dib's square names as headings; add one 'in plain words' line; write the answer itself in the client's words."
- **"Draft-first" needs a headless rule.** Add something like: "if the user can't be asked, state your read of the item and the sale as assumptions at the top, list every other guess, and mark the whole thing as a draft." Only Claude did this fully.
- **The Verify should check substance, not only shape.** Add: "every square names at least one concrete fact, price or channel from your business, and the conversion square leads to the sale you defined." As written, a thin plan (agy-pro WITH, overall 5.0) passes and a strong one (Claude WITHOUT, 9.0) fails.
- **Language:** the skill says nothing about the client's language. For a bilingual audience, say "write messages and scripts in the language(s) the customers speak". The Spanish scripts were what judges liked most in agy-flash WITHOUT.
- **Name the CSV layout precisely** (title row, 2 assumption rows, band row plus square row ×3). Agents got it from the SKILL.md, but Codex, which never fetched the SKILL.md, had only the story and produced a bare 3×3.

## Caveats
- One sample per cell. LLM nondeterminism alone can move a plan by ±1–2 points, so treat this as anecdote-level evidence.
- **Judging noise:**
  - All plans were judged in one long prompt per judge (78k characters), so order and comparison effects are possible. The order was a fixed shuffle and the same for every judge.
  - Two of the four judges come from Google, which is also the vendor of two of the four agents.
  - One judge (Sonnet) is a Claude model judging Claude plans. Results excluding same-vendor judges are given above.
- **The brief makes "the sale" easy.** That removes the case the story argues hardest for (an ambiguous sale). A second persona with an unclear sale (a nonprofit, an art project) would test step 1 properly.
- **Headless runs remove the interview**, which is half of the story's method. This experiment tests the "draft from context" half only.
- **The format grader is lenient** on dashes and case for the title (only agy-flash used upper case, "1-PAGE MARKETING PLAN — TALLER LENTO") and accepts square synonyms. It requires the item and the sale to be in the CSV above the grid, so Codex WITH, which had them only in plan.md, fails those checks.
- The marketing skills installed for Codex (`~/.agents/skills`) were visible to it in both arms.

## Files
- `client_brief.md`: the persona.
- `prompts/`: task, suffix, story.
- `run.sh`, `lane.sh`: the harness.
- `graders/grade_format.py`: Grading A.
- `judging/rubric.md`: the rubric.
- `judging/key.json`: the blind key.
- `judging/plans/P*.md`: what the judges saw.
- `judging/raw/*.txt`: the judges' raw output.
- `aggregate.py`: produces `results.json` and `table.md`.
- `runs/<agent>-<arm>/`: `prompt.txt`, `agent.log`, `meta.json`, `format.json`, and `out/plan.csv` and `out/plan.md`. The agy-pro WITH clone of worklore-skills is not included.
