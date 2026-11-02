"""TEST_ONLY exact historical type rejection; never installed or used by runtime."""

import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

ARCHIVE = Path(__file__).resolve().parents[2] / "fixtures/actual_binding/legacy_contracts.zip"
ARCHIVE_SHA256 = "a53ddbac195f273843af05e79235985823ecc954f50018d28e5e329297de14c7"


def validate_legacy_fixture(archive):
    if not archive.is_file() or sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        raise ValueError("historical fixture absent or corrupt")
    with ZipFile(archive) as z:
        source = json.loads(z.read("SOURCES.json"))
        rows = source["files"]
        expected = {r["relative_path"] for r in rows} | {"SOURCES.json", "SHA256SUMS"}
        if len(rows) != 9 or len(expected) != 11 or sorted(z.namelist()) != sorted(expected):
            raise ValueError("historical fixture inventory")
        for r in rows:
            raw = z.read(r["relative_path"])
            if sha256(raw).hexdigest() != r["sha256"]:
                raise ValueError("historical source hash")


def assert_old_exact_reference_rejected(archive=ARCHIVE, *, cwd=None):
    validate_legacy_fixture(archive)
    archive = archive.resolve()
    test_root = Path(__file__).resolve().parent
    src = test_root.parents[2] / "src"
    # No checkout root: the archive owns its historical top-level tests package.
    roots = [str(archive), str(src), str(test_root)]
    probe = (
        "import sys;sys.path[:0]=" + repr(roots) + "\n"
        "from contracts import ReferenceExpectation\n"
        "from seven_input_contracts import SevenInputReference\n"
        "from cyberpilot_autotune.diagnostics.actual_binding import assess_actual_binding\n"
        "from actual_binding_test_vectors import complete_vector\n"
        "from pathlib import Path\n"
        "archive=" + repr(str(archive)) + "\n"
        "modules={'contracts':'contracts.py','seven_input_contracts':'seven_input_contracts.py',"
        "'content':'content.py','pins':'pins.py','tests':'tests/__init__.py',"
        "'tests.deny_fd_v2':'tests/deny_fd_v2/__init__.py',"
        "'tests.deny_fd_v2.contracts':'tests/deny_fd_v2/contracts.py',"
        "'tests.deny_fd_v2.validation':'tests/deny_fd_v2/validation.py',"
        "'tests.deny_fd_v2.wire':'tests/deny_fd_v2/wire.py'}\n"
        "for name,path in modules.items():\n"
        " assert Path(sys.modules[name].__file__)==Path(archive)/path, name\n"
        "v=complete_vector()\n"
        "old=SevenInputReference(ReferenceExpectation('1'*32,'2'*32,'DFD02',"
        "'3'*64,'4'*64,'5'*64,'6'*64),'7'*64)\n"
        "assert type(old) is SevenInputReference\n"
        "try: assess_actual_binding(v.bundle,expected_pre=old,expected_post=v.post)\n"
        "except ValueError: print('OLD_EXACT_REFERENCE_REJECTED')\n"
        "else: raise AssertionError('foreign type accepted')\n"
    )
    run = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", probe],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        cwd=cwd,
    )
    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == "OLD_EXACT_REFERENCE_REJECTED"
