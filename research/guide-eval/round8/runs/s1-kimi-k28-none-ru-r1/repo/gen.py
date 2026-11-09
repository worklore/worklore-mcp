#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys

# Athlete threshold from Intervals (see README). HR corridors in plans are
# percentages of LTHR; the watch needs absolute bpm.
LTHR = 172


def hr_target(step):
    """HR corridor for a step as absolute bpm (Intervals workout_doc format)."""
    lo, hi = step["hr_pct"]
    return {"type": "HR", "value": f"{round(LTHR * lo / 100)}-{round(LTHR * hi / 100)}bpm"}


def build_step(step):
    out = {"duration": step["minutes"] * 60}
    if "hr_pct" in step:
        out["target"] = hr_target(step)
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
