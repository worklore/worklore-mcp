---
title: The 1-Page Marketing Plan as an agent skill — interview me, build the Sheet
date: 2026-09-01
tags: [agent-skills, marketing, google-sheets, claude-code, automation]
type: success
status: n/a
reproducible: true
stack: Agent skills / Google Sheets (Claude Code)
agent: Claude Code
model: claude-fable-5
image: https://worklore.dev/images/derivografia-plan-sheet.png
image_alt: A finished 1-Page Marketing Plan in a Google Sheet — a 3x3 grid with colored Before / During / After bands, built by an agent skill
---

# The 1-Page Marketing Plan as an agent skill — interview me, build the Sheet

I read Allan Dib's *The 1-Page Marketing Plan* and realized the only durable
output of a whole business plan is that one 3×3 grid — nine squares across
Before / During / After. So instead of filling it in by hand again, I taught my
agent to do it: a skill that interviews you and builds the grid as a formatted
Google Sheet you keep.

What made it *usable*, not just correct:

- **Draft-first, not a blank interrogation.** The blank page is the barrier — the
  agent drafts all nine squares from context, then refines them with you.
- **Define "the sale" before anything else.** For an art project, "conversion"
  isn't money — it's *participation*. Guess that wrong and half the plan rots, so
  the skill pins it down first.
- **Plain-language per square.** I'm not a marketer; "capture leads" meant nothing
  to me until the skill explained it inline.
- **A dumb-but-real one:** the Google Sheets API can't merge cells, and a narrow
  label column turns long text into unreadable skinny towers. The fix — wide equal
  columns, phases as full-width colored bands, tall wrapped rows.

I checked first: plenty of "explain the framework" skills exist, but none that
builds the actual Sheet. So I built that, and ran it cold on a friend's Biennale
walking-photography app ("one walk, one photograph"). It produced a genuinely
usable plan in one sitting — [here's the actual Sheet it made](https://docs.google.com/spreadsheets/d/1mpbXD3JUynFk6ws7nDvJ-BWATnE5MxE2PGEGZ1NMbOU/edit?usp=sharing).
My first three layouts were unreadable before the band layout stuck — failures
are welcome here.

## Reproduce this
Prerequisites: an AI coding agent (Claude Code, Cursor, Codex…) with shell access
and a Google Sheets capability — a Google Sheets / Docs MCP tool, or the Sheets
API via a library like `gspread`.

Your agent will need from you: your product in a sentence, and what "a sale /
conversion" means for you.

Steps:
1. Install the skill: clone `https://github.com/worklore/worklore-skills` and copy
   `skills/one-page-marketing-plan-sheet/` into `~/.claude/skills/` (or your
   agent's skills directory). No skills folder? Point your agent at the raw
   `SKILL.md` in that repo.
2. Tell your agent: "make me a 1-page marketing plan."
3. Answer the two assumptions it asks first — *the item* and *the sale* — then
   refine the nine squares it drafts for you.
4. It creates a formatted Google Sheet (title, assumptions, three colored phase
   bands, the nine filled squares). No Sheets tool available? It emits the same
   grid as a CSV to import.

Verify: you end with a Google Sheet titled "1-Page Marketing Plan — <your
business>", laid out as the 3×3 grid and filled with your own answers.
