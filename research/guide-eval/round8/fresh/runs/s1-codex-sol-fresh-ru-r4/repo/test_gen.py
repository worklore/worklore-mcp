import json
import unittest
from pathlib import Path

from gen import build_event, hr_target


class GeneratorTests(unittest.TestCase):
    def test_hr_target_keeps_both_corridor_bounds(self):
        self.assertEqual(
            hr_target({"hr_pct": [88, 93]}),
            {"units": "%lthr", "value": 90.5, "start": 88, "end": 93},
        )

    def test_plan_targets_survive_repeats(self):
        plan = json.loads(Path("plans/tempo-run.json").read_text())
        steps = build_event(plan)["workout_doc"]["steps"]
        self.assertEqual(steps[0]["hr"]["start"], 68)
        self.assertEqual(steps[0]["hr"]["end"], 75)
        self.assertEqual(steps[1]["reps"], 3)
        self.assertEqual(steps[1]["steps"][0]["hr"]["start"], 88)
        self.assertEqual(steps[1]["steps"][0]["hr"]["end"], 93)
        self.assertEqual(steps[1]["steps"][1]["hr"]["start"], 75)
        self.assertEqual(steps[1]["steps"][1]["hr"]["end"], 82)
        self.assertEqual(steps[2]["hr"]["start"], 65)
        self.assertEqual(steps[2]["hr"]["end"], 72)


if __name__ == "__main__":
    unittest.main()
