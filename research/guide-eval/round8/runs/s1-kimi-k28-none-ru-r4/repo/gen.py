#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json

HR corridors are sent as absolute bpm, not "%lthr": Intervals.icu exports
%lthr targets to Garmin as heart-rate zones, so the watch clips every step
to its own zone bands. Only "bpm" targets arrive as a custom range.
"""
import json
import sys


def hr_target(step, lthr):
    """HR corridor for a step, converted from % of LTHR to absolute bpm."""
    lo, hi = step["hr_pct"]
    return {"units": "bpm", "value": round(lo / 100 * lthr),
            "end": round(hi / 100 * lthr)}


def build_step(step, lthr):
    out = {"duration": step["minutes"] * 60}
    if "hr_pct" in step:
        out["hr"] = hr_target(step, lthr)
    if "label" in step:
        out["text"] = step["label"]
    return out


def build_doc(plan):
    lthr = plan.get("lthr")
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
