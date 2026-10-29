#!/usr/bin/env python3
"""Build an Intervals.icu event body from a plan file.

The workout is sent as Intervals workout text in `description`. Intervals
parses that into its own workout_doc (resolving %LTHR to bpm) and exports
each HR target to Garmin as an explicit bpm range.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    if lo == hi:
        return f"{lo}% LTHR"
    return f"{lo}-{hi}% LTHR"


def fmt_duration(minutes):
    if minutes == int(minutes):
        return f"{int(minutes)}m"
    return f"{int(minutes * 60)}s"


def build_step(step):
    parts = ["-"]
    if "label" in step:
        parts.append(step["label"])
    parts.append(fmt_duration(step["minutes"]))
    if "hr_pct" in step:
        parts.append(hr_target(step))
    return " ".join(parts)


def build_description(plan):
    sections = []
    for block in plan["steps"]:
        if "repeat" in block:
            lines = [f"{block['repeat']}x"]
            lines += [build_step(s) for s in block["steps"]]
        else:
            lines = [build_step(block)]
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


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
