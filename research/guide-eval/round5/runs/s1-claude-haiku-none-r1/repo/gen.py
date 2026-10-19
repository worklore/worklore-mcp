#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


def hr_target(step, lthr):
    """HR corridor for a step, resolved to absolute bpm from the athlete's LTHR.

    Sent as bpm rather than %lthr: the watch clamps %lthr targets to its own
    zone bands instead of showing the planned corridor.
    """
    lo, hi = step["hr_pct"]
    return {
        "units": "bpm",
        "value": round(lthr * lo / 100),
        "end": round(lthr * hi / 100),
    }


def build_step(step, lthr):
    out = {"duration": step["minutes"] * 60}
    if "hr_pct" in step:
        out["hr"] = hr_target(step, lthr)
    if "label" in step:
        out["text"] = step["label"]
    return out


def build_doc(plan):
    lthr = plan["lthr"]
    steps = []
    for block in plan["steps"]:
        if "repeat" in block:
            steps.append({
                "reps": block["repeat"],
                "steps": [build_step(s, lthr) for s in block["steps"]],
            })
        else:
            steps.append(build_step(block, lthr))
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
