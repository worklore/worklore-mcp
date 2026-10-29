#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


LTHR = 172  # Athlete's Lactate Threshold Heart Rate in bpm (override if needed)

def hr_target(step):
    """HR corridor for a step, converted to absolute bpm based on LTHR.

    The watch expects absolute BPM values; using percentage of LTHR caused the
    watch to map zones to its own predefined bands. By converting the percentage
    to BPM we get the intended ranges (e.g., 68‑75 % LTHR → 117‑129 bpm).
    """
    lo_pct, hi_pct = step["hr_pct"]
    lo_bpm = int(round(LTHR * lo_pct / 100))
    hi_bpm = int(round(LTHR * hi_pct / 100))
    return {"units": "bpm", "value": lo_bpm, "end": hi_bpm}


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
