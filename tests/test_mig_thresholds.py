import unittest

from infralens.data import Workload, sample_scenarios
from infralens.i18n import localize_findings
from infralens.rules import detect_bottlenecks


class MigThresholdTests(unittest.TestCase):
    def test_mig_finding_includes_threshold_data(self):
        scenario = sample_scenarios()["SMB Starter - L4 1-GPU Inference"]
        workloads = [Workload(name="infer-1", kind="inference", gpu_demand=1, vram_gb=8)]

        findings = detect_bottlenecks(scenario, workloads, profile="default")
        mig = next(f for f in findings if f.code == "mig_opportunity")

        self.assertIsNotNone(mig.data)
        self.assertEqual(mig.data["gpu_util_threshold"], 65)
        self.assertEqual(mig.data["vram_used_threshold_gb"], 90.0)

    def test_korean_localized_mig_message_mentions_thresholds(self):
        scenario = sample_scenarios()["SMB Starter - L4 1-GPU Inference"]
        workloads = [Workload(name="infer-1", kind="inference", gpu_demand=1, vram_gb=8)]

        findings = detect_bottlenecks(scenario, workloads, profile="default")
        localized = localize_findings(findings, "ko")
        mig = next(f for f in localized if f.code == "mig_opportunity")

        self.assertIn("<65%", mig.message)
        self.assertIn("<90GB", mig.message)


if __name__ == "__main__":
    unittest.main()
