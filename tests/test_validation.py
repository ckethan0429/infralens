import unittest

from infralens.validation import parse_env_vars, validate_execution_settings


class ValidationTests(unittest.TestCase):
    def test_parse_env_vars_valid_and_invalid_lines(self):
        raw = "A=1\nINVALID\nB=2\n=bad\n"
        envs, invalid = parse_env_vars(raw)
        self.assertEqual(envs, {"A": "1", "B": "2"})
        self.assertEqual(invalid, [2, 4])

    def test_validate_docker_image_required(self):
        result = validate_execution_settings(
            exec_env_ui="Docker",
            exec_entry="python train.py",
            exec_image="",
            exec_cpumode_ui="Auto",
            exec_cpumanual="",
            exec_envvars_raw="",
        )
        self.assertTrue(any("Docker image" in e for e in result.errors))

    def test_validate_manual_cpu_required(self):
        result = validate_execution_settings(
            exec_env_ui="Bare Metal",
            exec_entry="python train.py",
            exec_image="",
            exec_cpumode_ui="Manual",
            exec_cpumanual="",
            exec_envvars_raw="",
        )
        self.assertTrue(any("Manual CPU set" in e for e in result.errors))

    def test_validate_entry_required(self):
        result = validate_execution_settings(
            exec_env_ui="Bare Metal",
            exec_entry="   ",
            exec_image="",
            exec_cpumode_ui="Auto",
            exec_cpumanual="",
            exec_envvars_raw="",
        )
        self.assertTrue(any("Entry command" in e for e in result.errors))


if __name__ == "__main__":
    unittest.main()

