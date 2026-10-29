#!/usr/bin/env python3
"""Build an Intervals.icu workout event from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


def build_step(step):
    """Format a step in Intervals.icu's workout-builder syntax."""
    lo, hi = step["hr_pct"]
    label = f'{step["label"]} ' if step.get("label") else ""
    return f'- {label}{step["minutes"]}m {lo}-{hi}% LTHR'


def build_description(plan):
    blocks = []
    for block in plan["steps"]:
        if "repeat" in block:
            blocks.append("\n".join(
                [f'{block["repeat"]}x'] + [build_step(s) for s in block["steps"]]
            ))
        else:
            blocks.append(build_step(block))
    return "\n\n".join(blocks)


def build_event(plan):
    return {
        "category": "WORKOUT",
        "type": plan["sport"],
        "name": plan["name"],
        "start_date_local": plan["date"] + "T00:00:00",
        "description": build_description(plan),
    }


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        plan = json.load(f)
    json.dump(build_event(plan), sys.stdout, indent=2)
    print()
