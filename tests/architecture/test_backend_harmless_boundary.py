"""Repository-only opt-in guest harness, no installed/application/CI capability."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "compatibility/containment_backend_harmless"


def test_neutral_types_and_checker_have_no_operational_dependencies():
    for name in ("records.py", "validation.py", "host_cases.py", "reporting.py"):
        tree = ast.parse((PACKAGE / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = (
                    [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                assert not any(
                    x.split(".")[0]
                    in {
                        "os",
                        "subprocess",
                        "socket",
                        "ctypes",
                        "threading",
                        "multiprocessing",
                        "cereal",
                        "openpilot",
                        "cyberpilot_autotune",
                    }
                    for x in names
                )


def test_host_runner_has_one_fixed_subprocess_and_no_shell_or_host_policy():
    source = (PACKAGE / "vm_runner.py").read_text()
    tree = ast.parse(source)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    runs = [n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == "run"]
    assert len(runs) == 1
    assert not any(k.arg == "shell" for k in runs[0].keywords)
    assert not any(
        word in source
        for word in (
            "os.system",
            "ctypes",
            "socket",
            "unshare(",
            "bpf(",
            "mount(",
            "mknod(",
            "sudo",
        )
    )
    literals = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)]
    assert "tcg,thread=single" in literals and "-nic" in literals and "none" in literals


def test_no_default_ci_execution_or_installed_module_import():
    assert "containment_backend_harmless" not in (ROOT / ".github/workflows/ci.yml").read_text()
    for source in (ROOT / "src").rglob("*.py"):
        assert "containment_backend_harmless" not in source.read_text()


def test_guest_c_has_no_continue_or_arbitrary_payload_interface():
    broker = (PACKAGE / "host/broker.c").read_text()
    assert "SECCOMP_USER_NOTIF_FLAG_CONTINUE" not in broker
    assert "SECCOMP_ADDFD_FLAG_SEND" in broker
    assert "RESOLVE_IN_ROOT | RESOLVE_NO_MAGICLINKS" in broker
    assert "O_PATH | O_CREAT | O_TRUNC | O_APPEND | O_WRONLY | O_RDWR" in broker
    for path in (PACKAGE / "host").glob("*.c"):
        assert not any(
            word in path.read_text()
            for word in ("system(", "popen(", "mknod(", "connect(", "socket(", "Params")
        )
