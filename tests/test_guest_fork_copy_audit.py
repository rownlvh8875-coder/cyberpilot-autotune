"""Original observed bytes/source cohort cannot be fabricated from synthetic admission."""

import base64
import copy
import hashlib
import importlib
import importlib.util

import pytest


def api():
    assert importlib.util.find_spec("tests.guest_fork_copy.audit") is not None, (
        "missing observed audit"
    )
    return importlib.import_module("tests.guest_fork_copy.audit")


def test_six_actual_guests_keep_loss_abort_unknown_identity_and_authority_separate():
    result = api().validate()
    assert result["actual_cases"] == 6 and result["raw_copy_records"] == 1701
    assert result["local_failures"] == [0, 1, 264, 0, 0, 0]
    assert result["committed_stage_sequences"] == [[1, 2], [1], [], [1], [1], [1]]
    assert result["identity_complete"] == [False] * 6
    assert not result["source_bytes_verified"] and not result["assets_verified"]
    assert result["evidence_class"] == "OBSERVED_UNTRUSTED" and result["status"] == "BLOCKED"
    assert result["actual_global_drops"] is None and not result["runtime_qualified"]
    assert all(v is False for v in result["permissions"].values())


@pytest.mark.parametrize("field", ["kernel", "init", "actual_config", "baseline_kernel"])
def test_changed_build_input_cannot_pass_the_recorded_cohort(field):
    audit = api()
    data = audit.load(audit.BUILD)
    data[field]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        audit.validate_build(data)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.__setitem__("evidence_class", "SYNTHETIC_ONLY"),
        lambda d: d.__setitem__("runtime_qualified", True),
        lambda d: d.__setitem__("build_manifest_sha256", "0" * 64),
        lambda d: d["captures"].pop(),
        lambda d: d["captures"][0].__setitem__("case", "TASK_FAIL"),
        lambda d: d["captures"][0]["serial"].__setitem__("bytes", True),
        lambda d: d["captures"][0].__setitem__("serial_base64", "bad"),
        lambda d: d["captures"][0]["image"].__setitem__("sha256", "0" * 64),
        lambda d: d["baseline"].__setitem__("expected", "OBSERVED_COPY"),
    ],
)
def test_class_authority_and_original_byte_bindings_cannot_be_promoted_or_substituted(mutate):
    audit = api()
    data = audit.load(audit.ACTUAL)
    mutate(data)
    with pytest.raises(ValueError):
        audit.validate_actual(data, audit.BUILD.read_bytes())


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (b"kind=READ", b"kind=STORE"),
        (b"ofd=0", b"ofd=9"),
        (b"source=2 dest=5", b"source=9 dest=5"),
        (b"reason=TASK_INJECTED", b"reason=NONE"),
    ],
)
def test_rehashed_wrong_stage_unknown_identity_source_or_injection_cannot_match_observed_workload(
    before, after
):
    audit = api()
    data = copy.deepcopy(audit.load(audit.ACTUAL))
    row = data["captures"][4 if before == b"reason=TASK_INJECTED" else 0]
    raw = base64.b64decode(row["serial_base64"]).replace(before, after)
    row["serial_base64"] = base64.b64encode(raw).decode()
    row["serial"].update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError):
        audit.validate_actual(data, audit.BUILD.read_bytes())


def test_source_claim_or_path_drift_is_rejected_without_a_kernel_tree():
    audit = api()
    data = audit.load(audit.SOURCES)
    data["patched_files"][0]["ranges"][0]["start"] += 1
    with pytest.raises(ValueError):
        audit.validate_sources(data)
