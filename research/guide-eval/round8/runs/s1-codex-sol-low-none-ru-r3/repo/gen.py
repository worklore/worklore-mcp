#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys
from decimal import Decimal, ROUND_HALF_UP


def hr_target(step, lthr):
    """An absolute BPM corridor, expressed as center and half-width."""
    lo, hi = step["hr_pct"]
    if not 0 < lo <= hi:
        raise ValueError("hr_pct must contain increasing positive bounds")
    bounds = [int((Decimal(str(pct)) * Decimal(str(lthr)) / 100).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP)) for pct in (lo, hi)]
    return {"units": "bpm", "value": sum(bounds) / 2, "range": (bounds[1] - bounds[0]) / 2}


def build_step(step, lthr):
    out = {"duration": step["minutes"] * 60}
    if "hr_pct" in step:
        out["hr"] = hr_target(step, lthr)
    if "label" in step:
        out["text"] = step["label"]
    return out


def build_doc(plan):
    lthr = plan["lthr_bpm"]
    if lthr <= 0:
        raise ValueError("lthr_bpm must be positive")
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
