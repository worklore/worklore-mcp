#!/usr/bin/env python3
"""Shuffle the 8 plan.md files into P1..P8, redact identity, build the judge prompt.
The key stays in judging/key.json (never shown to judges)."""
import json, random, re
from pathlib import Path
D = Path(__file__).resolve().parent.parent
J = D / "judging"
runs = sorted(p.name for p in (D / "runs").iterdir() if (p / "out/plan.md").exists())
rng = random.Random(20261003)
order = runs[:]; rng.shuffle(order)
key = {f"P{i+1}": rid for i, rid in enumerate(order)}
(J / "key.json").write_text(json.dumps(key, indent=1))
RED = re.compile(r"\b(Claude( Code)?|Anthropic|Codex|OpenAI|ChatGPT|GPT[-\w.]*|Gemini[-\w.]*|Antigravity|Google DeepMind|worklore[\w./-]*|SKILL\.md|Allan Dib'?s?)\b", re.I)
parts = [(J / "rubric.md").read_text(), "\n=== CLIENT BRIEF ===\n", (D / "prompts/client_brief.md").read_text()]
(J / "plans").mkdir(exist_ok=True)
for pid, rid in key.items():
    t = RED.sub("[redacted]", (D / "runs" / rid / "out/plan.md").read_text(errors="replace"))
    (J / "plans" / f"{pid}.md").write_text(t)
    parts += [f"\n=== PLAN {pid} ===\n", t, f"\n=== END PLAN {pid} ===\n"]
parts.append("\nNow output the JSON object for P1..P%d." % len(key))
(J / "judge_prompt.md").write_text("".join(parts))
print(len(key), "plans;", len("".join(parts)), "chars")
