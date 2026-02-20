import unittest

from infralens.commands import ExecutionConfig, build_execution_templates
from infralens.data import default_workloads, sample_scenarios
from infralens.rules import build_placement_recommendation


class CommandTemplateTests(unittest.TestCase):
    def test_manual_cpu_set_and_extra_args_are_applied(self):
        scenario = sample_scenarios()["SMB Growth - L40s 2-GPU Hybrid"]
        rec = build_placement_recommendation(scenario, default_workloads(), 58)
        cfg = ExecutionConfig(
            environment="docker",
            entry_command="python train.py",
            image_name="demo:latest",
            container_prefix="demo",
            extra_args="--epochs 1",
            env_vars={"FOO": "bar"},
            cpu_set_mode="manual",
            manual_cpu_set="0-7",
            gpu_visibility_style="cuda_visible_devices",
        )

        templates = build_execution_templates(scenario, default_workloads(), rec, exec_cfg=cfg)
        self.assertTrue(templates)
        first = templates[0]
        self.assertIn("--cpuset-cpus=\"0-7\"", first.docker_cmd)
        self.assertIn("--epochs 1", first.docker_cmd)
        self.assertIn("-e FOO=bar", first.docker_cmd)

    def test_auto_cpu_set_used_when_manual_not_set(self):
        scenario = sample_scenarios()["H200 8-GPU Server"]
        rec = build_placement_recommendation(scenario, default_workloads(), 62)
        cfg = ExecutionConfig(cpu_set_mode="manual", manual_cpu_set="")

        templates = build_execution_templates(scenario, default_workloads(), rec, exec_cfg=cfg)
        self.assertTrue(templates)
        self.assertIn("taskset -c 0-23,48-71", templates[0].taskset_cmd)

    def test_docker_gpus_flag_and_newline_for_mig(self):
        scenario = sample_scenarios()["SMB Starter - L4 1-GPU Inference"]
        rec = build_placement_recommendation(scenario, default_workloads(), 40)
        cfg = ExecutionConfig(
            environment="docker",
            gpu_visibility_style="docker_gpus_device",
            entry_command="python train2.py",
        )
        templates = build_execution_templates(scenario, default_workloads(), rec, exec_cfg=cfg)
        self.assertTrue(templates)
        has_device_flag = any('--gpus "device=' in t.docker_cmd for t in templates)
        self.assertTrue(has_device_flag)
        has_mig_header = any("# MIG profile:" in t.docker_cmd for t in templates)
        if has_mig_header:
            sample = next(t for t in templates if "# MIG profile:" in t.docker_cmd)
            self.assertIn("\n", sample.docker_cmd)


if __name__ == "__main__":
    unittest.main()
