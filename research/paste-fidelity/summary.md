# Paste-hash test: does the text an agent sends to check_capability match the file?

216 runs. `exact` = byte-identical, so the returned sha256 describes the real file.

| phase | agent | runs | exact text | passed the url | whitespace only | truncated | changed | unusable path / no call | sent expected_sha256 | 75 KB file: median output tokens / wall s / $ |
|---|---|---|---|---|---|---|---|---|---|---|
| before | Claude Code · Opus 5.5 | 24 | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 27645 / 187.14 / 1.03 |
| before | Codex CLI · default | 24 | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 235 / 15.95 / – |
| before | Antigravity · Gemini 3.8 Flash high | 24 | 18 | 0 | 3 | 0 | 0 | 3 | 0 | 17442 / 300.71 / – |
| after-file | Claude Code · Opus 5.5 | 24 | 23 | 0 | 0 | 0 | 0 | 1 | 0 | 27800 / 187.86 / 1.03 |
| after-file | Codex CLI · default | 24 | 24 | 0 | 0 | 0 | 0 | 0 | 24 | 275 / 16.64 / – |
| after-file | Antigravity · Gemini 3.8 Flash high | 24 | 16 | 0 | 2 | 0 | 2 | 4 | 18 | 15893 / 300.58 / – |
| after-url | Claude Code · Opus 5.5 | 24 | 3 | 21 | 0 | 0 | 0 | 0 | 1 | 1599 / 21.42 / 0.25 |
| after-url | Codex CLI · default | 24 | 24 | 0 | 0 | 0 | 0 | 0 | 24 | 295 / 15.48 / – |
| after-url | Antigravity · Gemini 3.8 Flash high | 24 | 10 | 7 | 0 | 2 | 5 | 0 | 18 | 5323 / 55.75 / – |

## By file size (exact / runs, all agents)

| skill | bytes | claude | codex | gemini |
|---|---|---|---|---|
| example-command | 1,226 | 3/3 | 3/3 | 3/3 |
| playground | 3,824 | 3/3 | 3/3 | 0/3 |
| discord-configure | 4,324 | 3/3 | 3/3 | 3/3 |
| agent-development | 11,168 | 3/3 | 3/3 | 3/3 |
| build-mcp-app | 19,391 | 3/3 | 3/3 | 3/3 |
| skill-development | 22,825 | 3/3 | 3/3 | 3/3 |
| skill-creator | 33,168 | 3/3 | 3/3 | 3/3 |
| siege | 75,513 | 3/3 | 3/3 | 0/3 |

## Every non-exact run

### after-file · claude · siege r2 — no_call (sent None of 75513 bytes, None source lines lost/changed)

### after-file · gemini · build-mcp-app r2 — changed (sent 19396 of 19391 bytes, 1 source lines lost/changed)

```diff
--- 
+++ 
@@ -192 +192 @@
-- Load remote images reliably — inline as `data:` URLs server-side
+- snap/load remote images reliably — inline as `data:` URLs server-side
```

### after-file · gemini · discord-configure r1 — edge_whitespace (sent 4325 of 4324 bytes, 0 source lines lost/changed)

```diff
--- 
+++ 
@@ -99,0 +100 @@
+
```

### after-file · gemini · discord-configure r2 — edge_whitespace (sent 4325 of 4324 bytes, 0 source lines lost/changed)

```diff
--- 
+++ 
@@ -99,0 +100 @@
+
```

### after-file · gemini · skill-creator r3 — changed (sent 33172 of 33168 bytes, 4 source lines lost/changed)

```diff
--- 
+++ 
@@ -239,4 +239,4 @@
-     <workspace>/iteration-N \
-     --skill-name "my-skill" \
-     --benchmark <workspace>/iteration-N/benchmark.json \
-     > /dev/null 2>&1 &
+      <workspace>/iteration-N \
+      --skill-name "my-skill" \
+      --benchmark <workspace>/iteration-N/benchmark.json \
+      > /dev/null 2>&1 &
```

### after-url · gemini · build-mcp-app r2 — changed (sent 4 of 19391 bytes, 392 source lines lost/changed)

```diff
--- 
+++ 
@@ -1,392 +1 @@
----
-name: build-mcp-app
-description: This skill should be used when the user wants to build an "MCP app", add "interactive UI" or "widgets" to an MCP server, "render components in chat", build "MCP UI resources", make a tool that shows a "form", "picker", "dashboard" or "confirmation dialog" inline in the conversation, or mentions "apps SDK" in the context of MCP. Use AFTER the build-mcp-server skill has settled the deployment model, or when the user already knows they want UI widgets.
-version: 0.1.0
----
-
-# Build an MCP App (Interactive UI Widgets)
-
-An MCP app is a standard MCP server that **also serves UI resources** — interactive components rendered inline in the chat surface. Build once, runs in Claude *and* ChatGPT and any other host that implements the apps surface.
-
-The UI layer is **additive**. Under the hood it's still tools, resources, and the same wire protocol. If you haven't built a plain MCP server before, the `build-mcp-server` skill covers the base layer. This skill adds widgets on top.
-
-> **Testing in Claude:** Add the server as a custom connector in claude.ai (via a Cloudflare tunnel for local dev) — this exercises the real iframe sandbox and `hostContext`. See https://claude.com/docs/connectors/building/testing.
-
-## Claude host specifics
-
-| `_meta.ui.*` key | Where | Effect |
-|---|---|---|
-| `resourceUri` | tool | Which `ui://` resource the host renders for this tool's results. |
-| `visibility: ["app"]` | tool | 
```

### after-url · gemini · discord-configure r1 — truncated (sent 20 of 4324 bytes, 97 source lines lost/changed)

```diff
--- 
+++ 
@@ -3,97 +2,0 @@
-description: Set up the Discord channel — save the bot token and review access policy. Use when the user pastes a Discord bot token, asks to configure Discord, asks "how do I set this up" or "who can reach me," or wants to check channel status.
-user-invocable: true
-allowed-tools:
-  - Read
-  - Write
-  - Bash(ls *)
-  - Bash(mkdir *)
----
-
-# /discord:configure — Discord Channel Setup
-
-Writes the bot token to `~/.claude/channels/discord/.env` and orients the
-user on access policy. The server reads both files at boot.
-
-Arguments passed: `$ARGUMENTS`
-
----
-
-## Dispatch on arguments
-
-### No args — status and guidance
-
-Read both state files and give the user a complete picture:
-
-1. **Token** — check `~/.claude/channels/discord/.env` for
-   `DISCORD_BOT_TOKEN`. Show set/not-set; if set, show first 6 chars masked.
-
```

### after-url · gemini · siege r3 — changed (sent 5 of 75513 bytes, 732 source lines lost/changed)

```diff
--- 
+++ 
@@ -1,732 +1 @@
----
-name: siege
-description: "Work on one hard mathematics problem in rounds: each round a judge writes a few self-contained questions, independent workers answer them, and the judge keeps a ledger of what is proved, refuted and open, until the judge concludes or the rounds run out, and then a proof.md says plainly what is and is not proved. A run takes hours and dozens of worker runs. Usage: /math-proof:siege [NAME=value settings] <the problem, stated in full, or the path of a file holding it>."
-argument-hint: "[NAME=value ...] [DIR=run-directory] <problem statement | problem-file>"
-disable-model-invocation: true
-disallowed-tools: WebSearch, WebFetch, AskUserQuestion
-allowed-tools: Read, Write, Edit, Glob, Grep, Agent, Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/ledger.py *), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/siege/scripts/ledger.py *), Bash(python ${CLAUDE_SKILL_DIR}/scripts/ledger.py *), Bash(python ${CLAUDE_PLUGIN_ROOT}/skills/siege/scripts/ledger.py *), Bash(mkdir *), Bash(cp *), Bash(mv *), Bash(cat *), Bash(test *), Bash(ls *), Bash(wc *), Bash(cmp *), Bash(grep *), Bash(printf *), Bash(echo *)
----
-
-# math-proof: siege
-
-## The approach
-The skill works on one problem in at most MAX_ROUNDS rounds. Each round a judge writes a few self-contained
-questions, at most WAVE of them before round ESC_ROUND. The steps below call them queries. Each question goes
-to a fresh worker that sees only that question and the problem statement. T
```

### after-url · gemini · skill-creator r2 — changed (sent 4 of 33168 bytes, 485 source lines lost/changed)

```diff
--- 
+++ 
@@ -1,485 +1 @@
----
-name: skill-creator
-description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
----
-
-# Skill Creator
-
-A skill for creating new skills and iteratively improving them.
-
-At a high level, the process of creating a skill goes like this:
-
-- Decide what you want the skill to do and roughly how it should do it
-- Write a draft of the skill
-- Create a few test prompts and run claude-with-access-to-the-skill on them
-- Help the user evaluate the results both qualitatively and quantitatively
-  - While the runs happen in the background, draft some quantitative evals if there aren't any (if there are some, you can either use as is or modify if you feel something needs to change about them). Then explain them to the user (or if they already existed, explain the ones that already exist)
-  - Use the `eval-viewer/generate_review.py` script to show the user the results for them to look at, and also let them look at the quantitative metrics
-- Rewrite the skill based on feedback from the user's evaluation of the results (and also if there are any glaring flaws that become apparent from the quantitative benchmarks)
-- Repeat until you're satisfied
-- Expand the test set and try again
```

### after-url · gemini · skill-creator r3 — changed (sent 33172 of 33168 bytes, 4 source lines lost/changed)

```diff
--- 
+++ 
@@ -239,4 +239,4 @@
-     <workspace>/iteration-N \
-     --skill-name "my-skill" \
-     --benchmark <workspace>/iteration-N/benchmark.json \
-     > /dev/null 2>&1 &
+      <workspace>/iteration-N \
+      --skill-name "my-skill" \
+      --benchmark <workspace>/iteration-N/benchmark.json \
+      > /dev/null 2>&1 &
```

### after-url · gemini · skill-development r1 — truncated (sent 27 of 22825 bytes, 635 source lines lost/changed)

```diff
--- 
+++ 
@@ -3,635 +2,0 @@
-description: This skill should be used when the user wants to "create a skill", "add a skill to plugin", "write a new skill", "improve skill description", "organize skill content", or needs guidance on skill structure, progressive disclosure, or skill development best practices for Claude Code plugins.
-version: 0.1.0
----
-
-# Skill Development for Claude Code Plugins
-
-This skill provides guidance for creating effective skills for Claude Code plugins.
-
-## About Skills
-
-Skills are modular, self-contained packages that extend Claude's capabilities by providing
-specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific
-domains or tasks—they transform Claude from a general-purpose agent into a specialized agent
-equipped with procedural knowledge that no model can fully possess.
-
-### What Skills Provide
-
-1. Specialized workflows - Multi-step procedures for specific domains
-2. Tool integrations - Instructions for working with specific file formats or APIs
-3. Domain expertise - Company-specific knowledge, schemas, business logic
-4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks
-
-### Anatomy of a Skill
-
-Every skill consists of a required SKILL.md file and optional bundled resources:
-
-```
```

### after-url · gemini · skill-development r2 — changed (sent 4 of 22825 bytes, 637 source lines lost/changed)

```diff
--- 
+++ 
@@ -1,637 +1 @@
----
-name: skill-development
-description: This skill should be used when the user wants to "create a skill", "add a skill to plugin", "write a new skill", "improve skill description", "organize skill content", or needs guidance on skill structure, progressive disclosure, or skill development best practices for Claude Code plugins.
-version: 0.1.0
----
-
-# Skill Development for Claude Code Plugins
-
-This skill provides guidance for creating effective skills for Claude Code plugins.
-
-## About Skills
-
-Skills are modular, self-contained packages that extend Claude's capabilities by providing
-specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific
-domains or tasks—they transform Claude from a general-purpose agent into a specialized agent
-equipped with procedural knowledge that no model can fully possess.
-
-### What Skills Provide
-
-1. Specialized workflows - Multi-step procedures for specific domains
-2. Tool integrations - Instructions for working with specific file formats or APIs
-3. Domain expertise - Company-specific knowledge, schemas, business logic
-4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks
-
-### Anatomy of a Skill
-
-Every skill consists of a required SKILL.md file and optional bundled resources:
```

### before · gemini · playground r1 — edge_whitespace (sent 3823 of 3824 bytes, 0 source lines lost/changed)

### before · gemini · playground r2 — edge_whitespace (sent 3825 of 3824 bytes, 0 source lines lost/changed)

```diff
--- 
+++ 
@@ -76,0 +77 @@
+
```

### before · gemini · playground r3 — edge_whitespace (sent 3825 of 3824 bytes, 0 source lines lost/changed)

```diff
--- 
+++ 
@@ -76,0 +77 @@
+
```

