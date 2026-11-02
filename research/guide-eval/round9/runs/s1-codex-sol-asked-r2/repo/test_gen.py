import json
import unittest
from pathlib import Path

from gen import build_event


class HeartRateRangeTest(unittest.TestCase):
    def test_plan_preserves_each_hr_corridor_as_a_range(self):
        plan = json.loads(Path("plans/tempo-run.json").read_text())
        steps = build_event(plan)["workout_doc"]["steps"]

        self.assertEqual(steps[0]["hr"], {"units": "%lthr", "start": 68, "end": 75})
        self.assertEqual(steps[1]["reps"], 3)
        self.assertEqual(steps[1]["steps"][0]["hr"], {"units": "%lthr", "start": 88, "end": 93})
        self.assertEqual(steps[1]["steps"][1]["hr"], {"units": "%lthr", "start": 75, "end": 82})
        self.assertEqual(steps[2]["hr"], {"units": "%lthr", "start": 65, "end": 72})


if __name__ == "__main__":
    unittest.main()
