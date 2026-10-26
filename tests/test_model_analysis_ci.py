"""Regression tests for CI failure propagation and safe report rendering."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class ModelAnalysisCI(unittest.TestCase):
    def run_analyzer(self, source):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wrapper = root / "run_model_analysis_ci.sh"
            shutil.copyfile(Path(__file__).parents[1] / "scripts" / wrapper.name, wrapper)
            (root / "analyze_models.py").write_text(source)
            summary = root / "summary.md"
            result = subprocess.run(
                ["bash", str(wrapper)], capture_output=True, text=True,
                env={**os.environ, "RUNNER_TEMP": directory, "GITHUB_STEP_SUMMARY": str(summary)},
            )
            return result, summary.read_text()

    def test_success_is_preserved(self):
        result, summary = self.run_analyzer('print("[SUCCESS] validated")')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("validated", summary)

    def test_validation_failure_is_preserved(self):
        result, _ = self.run_analyzer('import sys; print("[FAIL] invalid model"); sys.exit(1)')
        self.assertEqual(result.returncode, 1)

    def test_crash_without_failure_marker_still_fails(self):
        result, summary = self.run_analyzer('raise RuntimeError("invalid input")')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("RuntimeError", summary)

    def test_other_nonzero_exit_is_preserved(self):
        result, _ = self.run_analyzer('import sys; sys.exit(7)')
        self.assertEqual(result.returncode, 7)

    def test_report_html_is_escaped(self):
        _, summary = self.run_analyzer('print("</pre><img src=x>")')
        self.assertIn("&lt;/pre&gt;&lt;img src=x&gt;", summary)
        self.assertNotIn("<img", summary)


if __name__ == "__main__":
    unittest.main()
