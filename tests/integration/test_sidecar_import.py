"""A fresh process imports optional modules without native dependencies or effects."""

import subprocess
import sys


def test_fresh_sidecar_import_creates_no_runtime_resource():
    code = """import builtins,socket,subprocess,threading
def forbidden(*args,**kwargs):raise AssertionError("IMPORT_SIDE_EFFECT")
builtins.open=forbidden
socket.socket=forbidden
subprocess.Popen=forbidden
threading.Thread.start=forbidden
from cyberpilot_autotune.integrations.carrot.sidecar import cli,config,source,runner,diagnostics
assert "openpilot.cereal.messaging" not in sys.modules
assert "cyberpilot_autotune.runtime.engine" not in sys.modules
assert "cyberpilot_autotune.core.residual" not in sys.modules
print("IMPORT_OK")
"""
    result = subprocess.run(
        [sys.executable, "-c", "import sys\n" + code], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "IMPORT_OK"
