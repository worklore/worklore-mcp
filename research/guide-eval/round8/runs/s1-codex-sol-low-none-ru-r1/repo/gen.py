#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


def bpm_range(step, lthr):
    """Convert the planned LTHR percentages to whole bpm for display."""
    lo, hi = step["hr_pct"]
    return round(lo * lthr / 100), round(hi * lthr / 100)


def build_step(step, lthr):
    out = {"duration": step["minutes"] * 60}
    label = step.get("label", "")
    if "hr_pct" in step:
        lo, hi = bpm_range(step, lthr)
        label = f"{label} | HR {lo}-{hi} bpm" if label else f"HR {lo}-{hi} bpm"
    if label:
        out["text"] = label
    return out


def build_doc(plan):
    steps = []
    lthr = plan["lthr_bpm"]
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
