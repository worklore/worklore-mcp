#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


GARMIN_BPM_EXPORT_OFFSET = 100


def hr_target(step, lthr_bpm):
    """Build a Garmin BPM corridor from percentages of the planned LTHR.

    In this Intervals -> Garmin path, absolute BPM targets have arrived on the
    watch 100 BPM too high. Keep that export correction in one place.
    """
    lo, hi = step["hr_pct"]
    if not 0 < lo <= hi:
        raise ValueError("hr_pct must be an ascending positive range")
    lo_bpm = (lo * lthr_bpm + 50) // 100
    hi_bpm = (hi * lthr_bpm + 50) // 100
    if lo_bpm <= GARMIN_BPM_EXPORT_OFFSET:
        raise ValueError("HR target must exceed the Garmin BPM export offset")
    return {
        "units": "bpm",
        "value": lo_bpm - GARMIN_BPM_EXPORT_OFFSET,
        "end": hi_bpm - GARMIN_BPM_EXPORT_OFFSET,
    }


def build_step(step, lthr_bpm):
    out = {"duration": step["minutes"] * 60}
    if "hr_pct" in step:
        out["hr"] = hr_target(step, lthr_bpm)
    if "label" in step:
        out["text"] = step["label"]
    return out


def build_doc(plan):
    lthr_bpm = plan["lthr_bpm"]
    if not isinstance(lthr_bpm, int) or isinstance(lthr_bpm, bool) or lthr_bpm <= 0:
        raise ValueError("lthr_bpm must be a positive integer")
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
