#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


# Athlete LTHR as set in Intervals (see README.md). Plan HR targets are
# percentages of this; they are converted to absolute bpm here, because the
# watch clamps %LTHR targets to its own zone bands at export.
LTHR = 172


def hr_target(step):
    """HR corridor for a step, converted from % of LTHR to absolute bpm."""
    lo, hi = step["hr_pct"]
    return {
        "units": "bpm",
        "start": round(LTHR * lo / 100),
        "end": round(LTHR * hi / 100),
    }


def build_step(step):
    out = {"duration": step["minutes"] * 60}
    if "hr_pct" in step:
        out["hr"] = hr_target(step)
    if "label" in step:
        out["text"] = step["label"]
    return out


def build_doc(plan):
    steps = []
    for block in plan["steps"]:
        if "repeat" in block:
            steps.append({
                "reps": block["repeat"],
                "steps": [build_step(s) for s in block["steps"]],
            })
        else:
            steps.append(build_step(block))
    return {"steps": steps}


def build_event(plan):
    return {
        "category": "WORKOUT",
        "type": plan["sport"],
        "name": plan["name"],
        "start_date_local": plan["date"] + "T00:00:00",
        "workout_doc": build_doc(plan),
    }


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        plan = json.load(f)
    json.dump(build_event(plan), sys.stdout, indent=2)
    print()
