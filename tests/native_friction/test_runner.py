"""The explicit native runner must not turn unexecuted tests into a success."""

import subprocess
import sys


def test_native_runner_is_present_for_the_mandatory_source_ci_command():
    command = [sys.executable, "-m", "compatibility.friction_native.run"]
    help_result = subprocess.run(command + ["--help"], capture_output=True, text=True)
    assert help_result.returncode == 0
    assert "--reference-checkout" in help_result.stdout
    missing_reference = subprocess.run(command, capture_output=True, text=True)
    assert missing_reference.returncode == 2
    assert "--reference-checkout" in missing_reference.stderr
