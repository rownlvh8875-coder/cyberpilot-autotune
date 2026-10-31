"""Frozen original CPB bytes and source cannot be promoted or substituted."""

import base64
import hashlib
import importlib
import importlib.util
import re

import pytest


def api():
    assert importlib.util.find_spec("tests.guest_bootstrap.audit") is not None, "missing CPB audit"
    return importlib.import_module("tests.guest_bootstrap.audit")


def test_ten_actual_guests_preserve_origin_gaps_and_immutable_permissions():
    result = api().validate()
    assert result["actual_cases"] == 10 and result["raw_events"] == 3524
    assert result["local_failures"] == [0, 1, 344, 0, 0, 0, 0, 0, 0, 0]
    assert result["first_copy_link_counts"] == [8, 6, 0, 0, 7, 8, 8, 8, 8, 8]
    assert result["unknown_present_reads"] == [0, 0, 0, 0, 2, 0, 0, 0, 0, 0]
    assert result["missing_origin_witness_ids"] == [[], [6], [], [], [], [], [], [], [], []]
    assert result["committed_stage_sequences"] == [
        [1, 2],
        [1, 2],
        [],
        [],
        [1, 2],
        [1, 2],
        [1, 2],
        [1],
        [1],
        [1],
    ]
    assert not result["source_bytes_verified"] and not result["assets_verified"]
    assert result["evidence_class"] == "OBSERVED_UNTRUSTED" and result["status"] == "BLOCKED"
    assert not result["allocation_history_complete"] and not result["runtime_qualified"]
    assert result["actual_global_drops"] is None and all(
        v is False for v in result["permissions"].values()
    )


@pytest.mark.parametrize("field", ["kernel", "init", "actual_config", "baseline_kernel"])
def test_build_cohort_drift_is_rejected_before_assets_are_read(field):
    audit = api()
    data = audit.load(audit.BUILD)
    data[field]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        audit.validate_build(data)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(evidence_class="SYNTHETIC_ONLY"),
        lambda d: d.update(runtime_qualified=True),
        lambda d: d.update(build_manifest_sha256="0" * 64),
        lambda d: d["captures"].pop(),
        lambda d: d["captures"][0].update(case="SEED_FAIL"),
        lambda d: d["captures"][0]["serial"].update(bytes=True),
        lambda d: d["captures"][0].update(serial_base64="bad"),
        lambda d: d["captures"][0]["image"].update(sha256="0" * 64),
        lambda d: d["baseline"].update(expected="BOOTSTRAP_READY"),
    ],
)
def test_actual_class_authority_count_and_original_byte_bindings_are_frozen(mutate):
    audit = api()
    data = audit.load(audit.ACTUAL)
    mutate(data)
    with pytest.raises(ValueError):
        audit.validate_actual(data, audit.BUILD.read_bytes())


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (b"origin=FIRST_OBSERVED", b"origin=ALLOCATION"),
        (b"scope=8 actor=1 task=8", b"scope=1 actor=1 task=8"),
        (b"ofd=6 origin=FIRST_OBSERVED", b"ofd=7 origin=FIRST_OBSERVED"),
        (b"kind=READ", b"kind=STORE"),
        (b"epoch=1", b"epoch=2"),
        (b"DRAINED_EMITTERS_ONLY", b"GLOBAL_QUIESCENCE_PROVEN"),
    ],
)
def test_rehashing_changed_origin_identity_stage_or_epoch_does_not_recreate_actual_evidence(
    before, after
):
    audit = api()
    data = audit.load(audit.ACTUAL)
    row = data["captures"][0]
    raw = base64.b64decode(row["serial_base64"]).replace(before, after)
    row["serial_base64"] = base64.b64encode(raw).decode()
    row["serial"].update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError):
        audit.validate_actual(data, audit.BUILD.read_bytes())


def test_static_source_claim_drift_rejected_without_prepared_kernel_tree():
    audit = api()
    data = audit.load(audit.SOURCES)
    data["patched_files"][0]["ranges"][0]["start"] += 1
    with pytest.raises(ValueError):
        audit.validate_sources(data)


def test_rehashed_valid_boot_nonce_change_is_not_the_frozen_original_capture():
    audit = api()
    data = audit.load(audit.ACTUAL)
    row = data["captures"][0]
    raw = base64.b64decode(row["serial_base64"])
    changed = re.sub(
        rb"boot_nonce=([0-9a-f]{32})",
        lambda m: b"boot_nonce=" + (b"f" if m[1][:1] != b"f" else b"e") + m[1][1:],
        raw,
    )
    assert changed != raw
    row["serial_base64"] = base64.b64encode(changed).decode()
    row["serial"].update(bytes=len(changed), sha256=hashlib.sha256(changed).hexdigest())
    with pytest.raises(ValueError, match="FROZEN_ORIGINAL_CAPTURE_BYTES_CHANGED"):
        audit.validate_actual(data, audit.BUILD.read_bytes())
