#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}


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


def describe_step(step):
    """One line of Intervals' text grammar: m = minutes, % LTHR for HR."""
    label = step.get("label", "").strip()
    if label[:1].isdigit():
        raise ValueError("label must not start with a digit: " + label)
    lo, hi = step["hr_pct"]
    return "- %s %dm %d-%d%% LTHR" % (label, step["minutes"], lo, hi)


def build_description(plan):
    lines = []
    for block in plan["steps"]:
        if "repeat" in block:
            lines += ["", "%dx" % block["repeat"]]
            lines += [describe_step(s) for s in block["steps"]]
            lines.append("")
        else:
            lines.append(describe_step(block))
    return "\n".join(lines).strip() + "\n"


def build_event(plan):
    return {
        "category": "WORKOUT",
        "type": plan["sport"],
        "name": plan["name"],
        "start_date_local": plan["date"] + "T00:00:00",
        "description": build_description(plan),
        "workout_doc": build_doc(plan),
    }


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        plan = json.load(f)
    json.dump(build_event(plan), sys.stdout, indent=2)
    print()
