"""New image bytes are data, never execution or accepted acquisition."""

import gzip
import importlib
import importlib.util
import os
import subprocess

import pytest


def image_api():
    assert importlib.util.find_spec("tests.deny_fd_v2_transport") is not None, (
        "transport package required"
    )
    return importlib.import_module("tests.deny_fd_v2_transport.image")


@pytest.mark.parametrize("case", ("", "DFD00", "DFD07", None, False))
def test_unknown_case_has_no_image(case):
    with pytest.raises(ValueError):
        image_api().init_bytes(case)


def test_fixed_init_has_no_telemetry_fallback():
    raw = image_api().init_bytes("DFD01")
    assert b"test -c /dev/ttyS1" in raw
    assert b"stty -F /dev/ttyS1 raw -echo -opost" in raw
    assert b"exec </dev/null >/dev/ttyS1" in raw
    assert b"--probe DFD01" in raw
    assert b"DFD2_EXEC" in raw
    assert b"9>" not in raw


def test_image_retains_unchanged_probe_bytes(monkeypatch):
    from tests.test_deny_fd_v2_harness_assets import synthetic_assets

    old, _, _ = synthetic_assets(monkeypatch)
    a = (
        importlib.import_module("tests.deny_fd_v2_transport.assets")
        if importlib.util.find_spec("tests.deny_fd_v2_transport")
        else None
    )
    assert a is not None, "transport package required"
    bundle = a.TransportAssets(old.preflight())
    raw = image_api().build_image(bundle, "DFD01")
    assert raw == image_api().build_image(bundle, "DFD01")
    archive = gzip.decompress(raw)
    assert bundle.base.probe in archive
    assert image_api().init_bytes("DFD01") in archive


@pytest.mark.skipif(os.name != "posix", reason="harmless host shell control-flow test")
@pytest.mark.parametrize("failure", ("device", "stty", "none"))
def test_guest_script_setup_failure_never_opens_telemetry_or_emits_markers(tmp_path, failure):
    # Only external guest dependencies are doubled; real shell redirection and
    # control flow execute against owned files, never a VM or the real probe.
    busybox = tmp_path / "busybox-double"
    busybox.write_text("""#!/bin/sh
case "$1" in
 mount) exit 0;;
 test) [ "$SETUP_FAILURE" != device ]; exit $?;;
 stty) [ "$SETUP_FAILURE" != stty ]; exit $?;;
 uname) echo synthetic-kernel; exit 0;;
 reboot) exit 0;;
esac
exit 2
""")
    probe = tmp_path / "harmless-writer"
    probe.write_text("#!/bin/sh\necho synthetic-telemetry\necho synthetic-diagnostic >&2\n")
    busybox.chmod(0o700)
    probe.chmod(0o700)
    telemetry = tmp_path / "telemetry"
    console = tmp_path / "console"
    raw = image_api().init_bytes("DFD01").decode()
    raw = raw.replace("/bin/busybox", str(busybox)).replace("/deny-fd-v2-probe", str(probe))
    raw = raw.replace("/dev/ttyS1", str(telemetry)).replace("/dev/ttyS0", str(console))
    script = tmp_path / "init-double.sh"
    script.write_text(raw)
    result = subprocess.run(
        ["/bin/sh", str(script)],
        env={**os.environ, "SETUP_FAILURE": failure},
        capture_output=True,
        timeout=5,
    )
    if failure != "none":
        assert result.returncode == 2
        assert not telemetry.exists()
        assert b"DFD2_EXEC" not in result.stdout + result.stderr
    else:
        assert result.returncode == 0
        assert (
            telemetry.read_bytes() == b"ACTUAL_GUEST_KERNEL=synthetic-kernel\nDFD2_EXEC\n"
            b"synthetic-telemetry\nDFD2_PROBE_EXIT=0\nDFD2_DONE\n"
        )
        assert console.read_bytes() == b"synthetic-diagnostic\n"
