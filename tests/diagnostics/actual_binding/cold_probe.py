"""TEST_ONLY prepared first-call observer. Not a producer, CLI reader or sandbox."""

import json
import sys
from pathlib import Path

sys.path[:0] = [str(Path(sys.argv[1]) / "src"), str(Path(__file__).resolve().parent)]

from actual_binding_test_vectors import clock, complete_vector, replace_document  # noqa: E402

from cyberpilot_autotune.diagnostics.actual_binding import assess_actual_binding  # noqa: E402

case = sys.argv[2]
if case == "incomplete":
    vector = complete_vector(raw_changes={"cli_stderr": None})
elif case == "reject":
    vector = replace_document(complete_vector(), "baseline", b"bad")
elif case == "incomparable":
    vector = complete_vector(header_changes={"exit": {"host_clock_context": clock(generation=1)}})
else:
    assert case == "consistent"
    vector = complete_vector()

forbidden_events = []
sha256_c_calls = 0


def audit(event, args):
    if (
        event == "open"
        or event
        in (
            "import",
            "exec",
            "compile",
            "os.system",
            "os.fork",
            "os.remove",
            "os.rename",
            "os.mkdir",
            "os.rmdir",
            "os.link",
            "os.symlink",
            "os.truncate",
        )
        or event.startswith(
            ("socket.", "subprocess.", "os.exec", "os.spawn", "os.posix_spawn", "ctypes.")
        )
    ):
        forbidden_events.append(event)
        raise AssertionError("forbidden first-call effect")


def profile(frame, event, arg):
    global sha256_c_calls
    if event == "c_call":
        name = getattr(arg, "__name__", "")
        module = getattr(arg, "__module__", "")
        if "sha256" in name:
            sha256_c_calls += 1
        if module in ("time", "_thread") or name in ("open", "system", "fork", "posix_spawn"):
            forbidden_events.append((module, name))
            raise AssertionError("forbidden first-call function")


sys.addaudithook(audit)
sys.setprofile(profile)
try:
    result = assess_actual_binding(
        vector.bundle, expected_pre=vector.pre, expected_post=vector.post
    )
finally:
    sys.setprofile(None)
print(
    json.dumps(
        dict(
            structural_status=result.structural_status,
            forbidden_events=forbidden_events,
            sha256_c_calls=sha256_c_calls,
            first_assessor_call_observed=True,
            native_kernel_qualified=False,
            fixture_kind="TEST_ONLY_NOT_REAL_EVIDENCE",
        )
    )
)
