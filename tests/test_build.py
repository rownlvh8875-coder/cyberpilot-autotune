import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from native_e_lab import build_native


@pytest.mark.parametrize("code", [0, 1])
def test_fixed_build_command_and_hash_binding(tmp_path, monkeypatch, code):
    monkeypatch.setattr(build_native, "__file__", str(tmp_path / "build_native.py"))
    calls = []

    def compile_only(command, check):
        calls.append(command)
        if code == 0:
            Path(command[-2]).write_bytes(b"SYNTHETIC_BUILD_OUTPUT")
        return SimpleNamespace(returncode=code)

    monkeypatch.setattr(build_native.subprocess, "run", compile_only)
    assert build_native.main() == code
    assert calls[0][:7] == ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-o"]
    if code == 0:
        assert len(calls) == 3 and calls[1][-1].endswith("/domain_supervisor.c")
        assert calls[2][-1].endswith("/domain_worker.c")
        assert (tmp_path / "supervisor.sha256").read_text().strip() == hashlib.sha256(
            b"SYNTHETIC_BUILD_OUTPUT"
        ).hexdigest()
    else:
        assert not (tmp_path / "supervisor.sha256").exists()
