import unittest

from infralens.data import workloads_for_scenario


class DataPresetTests(unittest.TestCase):
    def test_smb_starter_is_inference_heavy(self):
        ws = workloads_for_scenario("SMB Starter - L4 1-GPU Inference")
        kinds = [w.kind for w in ws]
        self.assertGreaterEqual(kinds.count("inference"), 2)

    def test_mid_market_training_has_training_workloads(self):
        ws = workloads_for_scenario("Mid-Market Training - H100 8-GPU")
        train = [w for w in ws if w.kind == "training"]
        self.assertTrue(train)
        self.assertGreaterEqual(sum(w.gpu_demand for w in train), 4)


if __name__ == "__main__":
    unittest.main()
