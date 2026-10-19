#!/usr/bin/env python3
"""Build an Intervals.icu event body (workout_doc) from a plan file.

Usage: python3 gen.py plans/tempo-run.json > event.json
"""
import json
import sys


def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR.

    The lower bound must be `start`, not `value`: `{value, end}` is FIT-exported
    as a Lap-HR / zone target, which the watch clamps to its own HR zones.
    `{start, end}` is exported as an Instant-HR corridor in the bpm Intervals
    computed from its own LTHR.
    """
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


def describe_duration(minutes):
    # Intervals text grammar: `m` is minutes, `s` is seconds (distance would be mtr/km).
    secs = round(minutes * 60)
    return f"{secs // 60}m" if secs % 60 == 0 else f"{secs}s"


def describe_step(step):
    label = step.get("label", "")
    if label[:1].isdigit():
        # A leading digit gets parsed as a duration and breaks the whole description.
        raise ValueError(f"step label must not start with a digit: {label!r}")
    parts = ["-"]
    if label:
        parts.append(label)
    parts.append(describe_duration(step["minutes"]))
    if "hr_pct" in step:
        lo, hi = step["hr_pct"]
        parts.append(f"{lo}-{hi}% LTHR")
    return " ".join(parts)


def build_description(plan):
    """Steps in Intervals' native text grammar, so they render in the web UI."""
    lines = []
    for block in plan["steps"]:
        if "repeat" in block:
            # Repeat blocks need blank lines around them.
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(f"{block['repeat']}x")
            lines.extend(describe_step(s) for s in block["steps"])
            lines.append("")
        else:
            lines.append(describe_step(block))
    return "\n".join(lines).strip() + "\n"


def build_event(plan):
    return {
        "category": "WORKOUT",
        "type": plan["sport"],
        "name": plan["name"],
        "description": build_description(plan),
        "start_date_local": plan["date"] + "T00:00:00",
        "workout_doc": build_doc(plan),
    }


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        plan = json.load(f)
    json.dump(build_event(plan), sys.stdout, indent=2)
    print()
