"""Actual-byte replay and fail-closed evidence metadata, no guest execution."""

import base64
import copy
import hashlib
import json

import pytest

from tests.guest_raw_lifetime import audit


def bundle():
    raw = audit.BUILD.read_bytes()
    return json.loads(raw), raw, audit.load(audit.ACTUAL)


def test_actual_three_cases_and_pristine_negative_replay_without_runtime_assets():
    report = audit.validate()
    assert report["actual_cases"] == 3
    assert report["raw_events"] == 25
    assert report["local_failures"] == [0, 1, 10]
    assert report["baseline_missing_interface"] is True
    assert report["kernel_source_bytes_verified"] is False
    assert report["assets_verified"] is False
    assert report["status"] == "BLOCKED"
    assert report["actual_global_drops"] is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["kernel"].__setitem__("sha256", "0" * 64),
        lambda d: d["init"].__setitem__("bytes", 779416.0),
        lambda d: d["sources"].pop(),
        lambda d: d["sources"][0].__setitem__("path", "../outside"),
        lambda d: d["source_archive"].__setitem__("sha256", "0" * 64),
        lambda d: d["permissions"].__setitem__("application_authorized", True),
        lambda d: d["permissions"].__setitem__("runtime_accepted", 0),
        lambda d: d.__setitem__("build_input_closure_qualified", True),
        lambda d: d.__setitem__("runtime_qualified", True),
        lambda d: d.__setitem__("vm_cohort_digest", "0" * 64),
        lambda d: d.__setitem__("patched_release", "host-kernel"),
        lambda d: d["actual_config"].__setitem__("path", "../config"),
    ],
)
def test_build_cohort_cannot_drift_or_promote_qualification(mutate):
    data, _, _ = bundle()
    mutate(data)
    with pytest.raises(ValueError):
        audit.validate_build(data)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["captures"].pop(),
        lambda d: d["captures"][1].__setitem__("case", "NORMAL"),
        lambda d: d["captures"][0]["serial"].__setitem__("bytes", True),
        lambda d: d["captures"][0].__setitem__("serial_base64", "bad"),
        lambda d: d["captures"][0]["image"].__setitem__("sha256", "0" * 64),
        lambda d: d.__setitem__("build_manifest_sha256", "0" * 64),
        lambda d: d.__setitem__("runtime_qualified", True),
        lambda d: d.__setitem__("evidence_class", "QUALIFIED"),
        lambda d: d["baseline"].__setitem__("expected", "OBSERVED"),
    ],
)
def test_original_capture_or_source_binding_cannot_be_replaced(mutate):
    _, raw, data = bundle()
    mutate(data)
    with pytest.raises(ValueError):
        audit.validate_actual(data, raw)


def test_rehashed_wrong_stage_or_unknown_root_cannot_match_fixed_raw_workload():
    _, raw, original = bundle()
    for before, after in ((b"kind=FILE_NEW", b"kind=TABLE_NEW"), (b"table=0", b"table=1")):
        data = copy.deepcopy(original)
        row = data["captures"][0]
        serial = base64.b64decode(row["serial_base64"]).replace(before, after)
        row["serial_base64"] = base64.b64encode(serial).decode()
        row["serial"]["sha256"] = hashlib.sha256(serial).hexdigest()
        row["serial"]["bytes"] = len(serial)
        with pytest.raises(ValueError):
            audit.validate_actual(data, raw)


def test_source_range_metadata_is_pinned_even_when_kernel_tree_is_absent():
    sources = audit.load(audit.SOURCES)
    sources["patched_files"][0]["ranges"][0]["start"] += 1
    with pytest.raises(ValueError, match="SOURCE_REFERENCE_DRIFT"):
        audit.validate_sources(sources)
