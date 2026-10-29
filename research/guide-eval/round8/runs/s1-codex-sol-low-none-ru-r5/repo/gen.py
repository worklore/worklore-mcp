#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys
from decimal import Decimal, ROUND_HALF_UP


def hr_target(step, lthr):
    """Encode a planned LTHR corridor as absolute Garmin HR targets.

    Intervals' bpm target values are exported 100 bpm above the supplied
    numbers, so subtract that offset after calculating the actual bpm bounds.
    """
    lo, hi = step["hr_pct"]
    def encoded_bpm(pct):
        bpm = (Decimal(str(pct)) * Decimal(str(lthr)) / 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        return int(bpm) - 100

    return {"units": "bpm", "value": encoded_bpm(lo), "end": encoded_bpm(hi)}


def build_step(step, lthr):
    out = {"duration": step["minutes"] * 60}
    if "hr_pct" in step:
        out["hr"] = hr_target(step, lthr)
    if "label" in step:
        out["text"] = step["label"]
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
