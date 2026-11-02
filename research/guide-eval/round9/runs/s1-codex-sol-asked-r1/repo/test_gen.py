import json
import unittest
from pathlib import Path

from gen import build_event


class GeneratorTests(unittest.TestCase):
    def test_hr_corridors_including_repeated_steps(self):
        plan = json.loads(Path("plans/tempo-run.json").read_text())
        steps = build_event(plan)["workout_doc"]["steps"]
        targets = [steps[0]["hr"], *(s["hr"] for s in steps[1]["steps"]), steps[2]["hr"]]

        self.assertEqual(targets, [
            {"units": "%lthr", "start": 68, "end": 75},
            {"units": "%lthr", "start": 88, "end": 93},
            {"units": "%lthr", "start": 75, "end": 82},
            {"units": "%lthr", "start": 65, "end": 72},
        ])
        self.assertEqual(steps[1]["reps"], 3)


if __name__ == "__main__":
    unittest.main()
