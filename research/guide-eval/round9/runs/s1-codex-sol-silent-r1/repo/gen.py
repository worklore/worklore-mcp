#!/usr/bin/env python3
"""Build an Intervals.icu workout event from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


def build_step(step):
    """Use workout-builder syntax so Intervals parses the HR range itself."""
    parts = ["-"]
    if "label" in step:
        parts.append(step["label"])
    parts.append(f'{step["minutes"]}m')
    if "hr_pct" in step:
        lo, hi = step["hr_pct"]
        parts.append(f"{lo}-{hi}% LTHR")
    return " ".join(parts)


def build_description(plan):
    chunks = []
    consecutive_steps = []
    for block in plan["steps"]:
        if "repeat" in block:
            if consecutive_steps:
                chunks.append("\n".join(consecutive_steps))
                consecutive_steps = []
            chunks.append("\n".join(
                [f'{block["repeat"]}x'] + [build_step(s) for s in block["steps"]]
            ))
        else:
            consecutive_steps.append(build_step(block))
    if consecutive_steps:
        chunks.append("\n".join(consecutive_steps))
    return "\n\n".join(chunks)


def build_event(plan):
    return {
        "category": "WORKOUT",
        "type": plan["sport"],
        "name": plan["name"],
        "start_date_local": plan["date"] + "T00:00:00",
        "target": "HR",
        "description": build_description(plan),
    }


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        plan = json.load(f)
    json.dump(build_event(plan), sys.stdout, indent=2)
    print()
