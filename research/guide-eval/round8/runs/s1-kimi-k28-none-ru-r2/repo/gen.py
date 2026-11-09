#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


def hr_target(step, lthr):
    """HR corridor as absolute bpm, converted from % of LTHR.

    %LTHR corridors get clipped to the watch's own HR zone bands at export,
    so plans are converted to absolute bpm here; the watch then shows the
    exact corridor regardless of its own zones/LTHR.
    """
    lo, hi = step["hr_pct"]
    return {
        "units": "bpm",
        "min": round(lo * lthr / 100),
        "max": round(hi * lthr / 100),
    }


def build_step(step, lthr):
    out = {"duration": step["minutes"] * 60}
    if "hr_pct" in step:
        out["target"] = hr_target(step, lthr)
    if "label" in step:
        out["text"] = step["label"]
    return out


def build_doc(plan):
    steps = []
    for block in plan["steps"]:
        if "repeat" in block:
            steps.append({
                "reps": block["repeat"],
                "steps": [build_step(s, plan["lthr"]) for s in block["steps"]],
            })
        else:
            steps.append(build_step(block, plan["lthr"]))
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
