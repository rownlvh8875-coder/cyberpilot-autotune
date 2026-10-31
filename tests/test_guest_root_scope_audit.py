"""Original-byte/source-role evidence replay only; no VM or kernel build."""

import base64
import copy
import hashlib
import importlib
import importlib.util

import pytest


def api():
    assert importlib.util.find_spec("tests.guest_root_scope.audit") is not None, (
        "missing byte audit"
    )
    return importlib.import_module("tests.guest_root_scope.audit")


def test_three_actual_guests_keep_missing_root_provenance_and_loss_distinct():
    report = api().validate()
    assert report["raw_events"] == 37
    assert report["local_failures"] == [0, 1, 16]
    assert report["root_creation_observed"] == [True, False, False]
    assert report["actual_cases"] == 3 and report["baseline_missing_interface"]
    assert not report["kernel_source_bytes_verified"] and not report["assets_verified"]
    assert report["status"] == "BLOCKED" and report["actual_global_drops"] is None
    assert all(v is False for v in report["permissions"].values())


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["kernel"].__setitem__("sha256", "0" * 64),
        lambda d: d["sources"].pop(),
        lambda d: d["sources"][0].__setitem__("path", "../../outside"),
        lambda d: d["permissions"].__setitem__("application_authorized", True),
        lambda d: d["permissions"].__setitem__("runtime_accepted", 0),
        lambda d: d.__setitem__("build_input_closure_qualified", True),
        lambda d: d.__setitem__("runtime_qualified", True),
        lambda d: d["actual_config"].__setitem__("bytes", 1.0),
    ],
)
def test_frozen_build_metadata_cannot_gain_authority_or_change_input_cohort(mutate):
    audit = api()
    data = audit.load(audit.BUILD)
    mutate(data)
    with pytest.raises(ValueError):
        audit.validate_build(data)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["captures"].pop(),
        lambda d: d["captures"][0].__setitem__("case", "SMALL_BUFFER"),
        lambda d: d["captures"][0]["serial"].__setitem__("bytes", True),
        lambda d: d["captures"][0].__setitem__("serial_base64", "bad"),
        lambda d: d["captures"][0]["image"].__setitem__("sha256", "0" * 64),
        lambda d: d.__setitem__("build_manifest_sha256", "0" * 64),
        lambda d: d.__setitem__("runtime_qualified", True),
        lambda d: d.__setitem__("evidence_class", "QUALIFIED"),
        lambda d: d["baseline"].__setitem__("expected", "OBSERVED_ROOT_BIRTH"),
    ],
)
def test_original_byte_bindings_and_unqualified_class_are_required(mutate):
    audit = api()
    data = audit.load(audit.ACTUAL)
    mutate(data)
    with pytest.raises(ValueError):
        audit.validate_actual(data, audit.BUILD.read_bytes())


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (b"kind=TASK_ALLOC", b"kind=TASK_COMMIT"),
        (b"actor=0 task=1", b"actor=1 task=1"),
        (b"task=4", b"task=1"),
        (b"table=2", b"table=99"),
        (b"seq=1 kind=TASK_ALLOC", b"seq=2 kind=TASK_ALLOC"),
        (b"CPS_META version=1", b"CPS_META version=2"),
    ],
)
def test_rehashed_wrong_stage_actor_subject_namespace_or_version_does_not_match_source_workload(
    before, after
):
    audit = api()
    data = copy.deepcopy(audit.load(audit.ACTUAL))
    row = data["captures"][0]
    raw = base64.b64decode(row["serial_base64"]).replace(before, after)
    row["serial_base64"] = base64.b64encode(raw).decode()
    row["serial"].update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError):
        audit.validate_actual(data, audit.BUILD.read_bytes())


def test_source_ranges_are_pinned_even_without_prepared_source_tree():
    audit = api()
    data = audit.load(audit.SOURCES)
    data["patched_files"][0]["ranges"][0]["start"] += 1
    with pytest.raises(ValueError, match="SOURCE_REFERENCE_DRIFT"):
        audit.validate_sources(data)
