#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR.

    Intervals' workout_doc encodes a range as start/end; "value" is a single
    target. A {"value", "end"} mix is read as a single value, which the Garmin
    export snaps to one of the watch's own HR zones instead of our corridor.
    """
    lo, hi = step["hr_pct"]
    if lo == hi:
        return {"units": "%lthr", "value": lo}
    return {"units": "%lthr", "start": min(lo, hi), "end": max(lo, hi)}


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
