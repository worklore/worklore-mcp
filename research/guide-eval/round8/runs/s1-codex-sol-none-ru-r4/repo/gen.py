#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys
from decimal import Decimal, ROUND_HALF_UP


def bpm(percent, lthr_bpm):
    """Round a percentage of LTHR to the nearest whole beat per minute."""
    return int((Decimal(str(percent)) * Decimal(str(lthr_bpm)) / 100).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    ))


def build_step(step, lthr_bpm):
    out = {"duration": step["minutes"] * 60}
    label = step.get("label", "")
    if "hr_pct" in step:
        lo, hi = step["hr_pct"]
        if not 0 < lo <= hi:
            raise ValueError(f"invalid hr_pct range: {step['hr_pct']}")
        corridor = f"{bpm(lo, lthr_bpm)}-{bpm(hi, lthr_bpm)} bpm"
        label = f"{label} ({corridor})" if label else corridor
    if label:
        out["text"] = label
    return out


def build_doc(plan):
    lthr_bpm = plan["lthr_bpm"]
    if lthr_bpm <= 0:
        raise ValueError("lthr_bpm must be positive")
    steps = []
    for block in plan["steps"]:
        if "repeat" in block:
            steps.append({
                "reps": block["repeat"],
                "steps": [build_step(s, lthr_bpm) for s in block["steps"]],
            })
        else:
            steps.append(build_step(block, lthr_bpm))
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
