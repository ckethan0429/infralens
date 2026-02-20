import unittest

from infralens.commands import ExecutionConfig, build_execution_templates
from infralens.data import default_workloads, sample_scenarios
from infralens.rules import build_placement_recommendation


class SmokeTests(unittest.TestCase):
    def test_recommendation_and_templates_smoke(self):
        scenario = sample_scenarios()["SMB Growth - L40s 2-GPU Hybrid"]
        workloads = default_workloads()
        rec = build_placement_recommendation(scenario, workloads, 55)
        cfg = ExecutionConfig(environment="bare_metal", entry_command="python train.py")
        templates = build_execution_templates(scenario, workloads, rec, exec_cfg=cfg)
        self.assertIsInstance(templates, list)


if __name__ == "__main__":
    unittest.main()

