import json
import unittest
from pathlib import Path

from gen import build_event


class GeneratorTest(unittest.TestCase):
    def test_tempo_run_uses_native_hr_ranges(self):
        plan = json.loads(Path("plans/tempo-run.json").read_text())
        event = build_event(plan)

        self.assertEqual(event["target"], "HR")
        self.assertNotIn("workout_doc", event)
        self.assertEqual(event["description"], "\n\n".join([
            "- 10m 68-75% LTHR Warm-up easy",
            "3x\n- 8m 88-93% LTHR Tempo\n- 2m 75-82% LTHR Float",
            "- 5m 65-72% LTHR Cool-down",
        ]))


if __name__ == "__main__":
    unittest.main()
