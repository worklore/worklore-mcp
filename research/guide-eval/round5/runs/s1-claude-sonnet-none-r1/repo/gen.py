#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


def fmt_minutes(minutes):
    return f"{minutes}m"


def build_line(step):
    """One workout-syntax line: '- <label> 10m 68-75% LTHR'."""
    parts = ["-"]
    if "label" in step:
        parts.append(step["label"])
    parts.append(fmt_minutes(step["minutes"]))
    if "hr_pct" in step:
        lo, hi = step["hr_pct"]
        parts.append(f"{lo}-{hi}% LTHR")
    return " ".join(parts)


def build_description(plan):
    """Intervals.icu workout text; the server parses it into workout_doc."""
    blocks = []
    for block in plan["steps"]:
        if "repeat" in block:
            lines = [f"{block['repeat']}x"]
            lines += [build_line(s) for s in block["steps"]]
        else:
            lines = [build_line(block)]
        blocks.append("\n".join(lines))
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
