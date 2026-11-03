"""Value-boundary regressions: removing an exact/frozen/priority guard must fail."""

import importlib
import importlib.util
from dataclasses import FrozenInstanceError, fields, replace
from enum import Enum

import pytest


def values():
    assert importlib.util.find_spec("cyberpilot_autotune.diagnostics.actual_binding") is not None, (
        "neutral package missing"
    )
    return importlib.import_module("cyberpilot_autotune.diagnostics.actual_binding.values")


def pre_kwargs():
    return dict(
        contract_version="actual-diagnostic-prelaunch-reference-v1",
        workflow_run_id="1" * 32,
        workflow_attempt_id="2" * 32,
        case="DFD02",
        host_clock_cohort_sha256="3" * 64,
        host_clock_generation=0,
        baseline_sha256="4" * 64,
        command_sha256="5" * 64,
        preflight_sha256="6" * 64,
    )


def post_kwargs():
    return dict(
        contract_version="actual-diagnostic-capture-reference-v1",
        workflow_run_id="1" * 32,
        workflow_attempt_id="2" * 32,
        case="DFD02",
        pre_reference_content_sha256="7" * 64,
        intent_sha256="8" * 64,
        exit_sha256="9" * 64,
        snapshot_sha256="a" * 64,
    )


def test_exact_values_are_frozen():
    m = values()
    objects = (
        m.PrelaunchExpectedReference(**pre_kwargs()),
        m.CaptureFreezeExpectedReference(**post_kwargs()),
        m.ActualDiagnosticBundle((("baseline", b"{}"),), (("cli_stderr", b""),)),
        m.ActualBindingAssessment("REPORTED_BINDING_CONSISTENT", (), ()),
    )
    for obj in objects:
        assert not hasattr(obj, "__dict__")
        with pytest.raises(FrozenInstanceError):
            setattr(obj, fields(obj)[0].name, None)
        with pytest.raises(TypeError):
            replace(obj, permissions=(("application_authorized", True),))


def test_none_zero_and_bool_are_distinct():
    cls = values().PrelaunchExpectedReference
    missing = cls(**(pre_kwargs() | {"host_clock_generation": None}))
    zero = cls(**pre_kwargs())
    assert missing != zero and zero.host_clock_generation == 0
    for v in (False, True, -1, 2**64, 0.0, float("nan"), float("inf"), "0"):
        with pytest.raises(ValueError):
            cls(**(pre_kwargs() | {"host_clock_generation": v}))
    for n in (0, 2**64 - 1):
        assert cls(**(pre_kwargs() | {"host_clock_generation": n})).host_clock_generation == n


@pytest.mark.parametrize("name", tuple(pre_kwargs()))
@pytest.mark.parametrize("bad", ([], {}, b"bad", object()))
def test_pre_fields_reject_wrong_types(name, bad):
    with pytest.raises(ValueError):
        values().PrelaunchExpectedReference(**(pre_kwargs() | {name: bad}))


@pytest.mark.parametrize("name", tuple(post_kwargs()))
@pytest.mark.parametrize("bad", (False, 1, [], b"bad"))
def test_post_fields_reject_wrong_types(name, bad):
    with pytest.raises(ValueError):
        values().CaptureFreezeExpectedReference(**(post_kwargs() | {name: bad}))


@pytest.mark.parametrize(
    "field,bad",
    (
        ("contract_version", "future"),
        ("workflow_run_id", "A" * 32),
        ("workflow_attempt_id", "0" * 31),
        ("case", "DFD07"),
        ("case", " DFD02"),
        ("baseline_sha256", "x" * 64),
    ),
)
def test_reference_format_no_coercion(field, bad):
    with pytest.raises(ValueError):
        values().PrelaunchExpectedReference(**(pre_kwargs() | {field: bad}))


def test_subclasses_rejected_before_hooks():
    m = values()
    touched = []

    class TrapStr(str):
        def __eq__(self, other):
            touched.append("eq")
            raise AssertionError("foreign equality hook")

        __hash__ = str.__hash__

    class TrapTuple(tuple):
        def __iter__(self):
            touched.append("iter")
            raise AssertionError("foreign iterator")

    class TrapBytes(bytes):
        def __len__(self):
            touched.append("len")
            raise AssertionError("foreign bytes hook")

    class TrapInt(int):
        def __ge__(self, other):
            touched.append("compare")
            raise AssertionError("foreign number hook")

    Label = Enum("Label", {"CASE": "DFD02"}, type=str)

    for field, bad in (
        ("case", TrapStr("DFD02")),
        ("case", Label.CASE),
        ("contract_version", TrapStr("actual-diagnostic-prelaunch-reference-v1")),
        ("baseline_sha256", TrapStr("4" * 64)),
    ):
        with pytest.raises(ValueError):
            m.PrelaunchExpectedReference(**(pre_kwargs() | {field: bad}))
    for pairs in (
        TrapTuple(()),
        (TrapTuple(("x", b"")),),
        ((TrapStr("x"), b""),),
        (("x", TrapBytes(b"")),),
    ):
        with pytest.raises(ValueError):
            m.ActualDiagnosticBundle(pairs, ())
    with pytest.raises(ValueError):
        m.PrelaunchExpectedReference(**(pre_kwargs() | {"host_clock_generation": TrapInt(0)}))
    for state, reasons, skipped in (
        (TrapStr("REJECTED"), ("PARSE_INVALID",), ()),
        ("REJECTED", TrapTuple(("PARSE_INVALID",)), ()),
        ("REJECTED", (TrapStr("PARSE_INVALID"),), ()),
        ("REJECTED", ("PARSE_INVALID",), (TrapStr("clocks"),)),
    ):
        with pytest.raises(ValueError):
            m.ActualBindingAssessment(state, reasons, skipped)
    assert touched == []


@pytest.mark.parametrize(
    "pairs",
    (
        [],
        [("x", b"")],
        (["x", b""],),
        (("x",),),
        ((1, b""),),
        (("x", bytearray()),),
        (("x", memoryview(b"")),),
    ),
)
def test_bundle_rejects_mutable_or_wrong_elements(pairs):
    with pytest.raises(ValueError):
        values().ActualDiagnosticBundle(pairs, ())


def test_bundle_storage_does_not_coerce_roles():
    m = values()
    d = (("unknown", None), ("unknown", b""))
    value = m.ActualDiagnosticBundle(d, ())
    assert value.documents == d
    assert value.documents[0][1] is None and value.documents[1][1] == b""


def test_nullable_references_are_partial_values_not_factories():
    m = values()
    pre = pre_kwargs()
    for key in (
        "host_clock_cohort_sha256",
        "host_clock_generation",
        "baseline_sha256",
        "command_sha256",
        "preflight_sha256",
    ):
        pre[key] = None
    post = post_kwargs()
    for key in ("pre_reference_content_sha256", "intent_sha256", "exit_sha256", "snapshot_sha256"):
        post[key] = None
    assert m.PrelaunchExpectedReference(**pre).baseline_sha256 is None
    assert m.CaptureFreezeExpectedReference(**post).snapshot_sha256 is None


def test_reference_stored_fields_all_mandatory():
    m = values()
    for cls, kwargs in (
        (m.PrelaunchExpectedReference, pre_kwargs()),
        (m.CaptureFreezeExpectedReference, post_kwargs()),
    ):
        for name in kwargs:
            subset = dict(kwargs)
            del subset[name]
            with pytest.raises(TypeError):
                cls(**subset)


def test_assessment_fixed_facets():
    m = values()
    for state, reasons in (
        ("REJECTED", ("PARSE_INVALID",)),
        ("INCOMPLETE", ("MISSING_RAW",)),
        ("REPORTED_TIME_ORDER_UNCOMPARABLE", ("CLOCK_CONTEXT_CHANGED",)),
        ("REPORTED_BINDING_CONSISTENT", ()),
    ):
        r = m.ActualBindingAssessment(state, reasons, ())
        assert r.status == "BLOCKED" and r.content_status == "NOT_EVALUATED"
        assert r.provenance == "BLOCKED_NO_INDEPENDENT_VERIFICATION"
        assert r.history == "UNAVAILABLE" and r.integrated_admission is False
        assert len(r.permissions) == 9 and all(v is False for _, v in r.permissions)


@pytest.mark.parametrize(
    "state,reasons,skipped",
    (
        ("REPORTED_BINDING_CONSISTENT", (), ("clocks",)),
        ("REJECTED", (), ()),
        ("INCOMPLETE", ("WRONG_ORIGIN",), ()),
        ("REPORTED_TIME_ORDER_UNCOMPARABLE", ("MISSING_RAW", "CLOCK_CONTEXT_CHANGED"), ()),
        ("REJECTED", ("HASH_MISMATCH", "PARSE_INVALID"), ()),
        ("REJECTED", ("PARSE_INVALID", "PARSE_INVALID"), ()),
        ("REJECTED", ["PARSE_INVALID"], ()),
        ("REJECTED", ("bad",), ()),
        ("REJECTED", ("PARSE_INVALID",), ("clocks", "assets")),
        ("REJECTED", ("PARSE_INVALID",), ("bad",)),
        ("REJECTED", ("PARSE_INVALID",), ("clocks", "clocks")),
        ("future", (), ()),
    ),
)
def test_result_rejects_incoherent_or_unordered_fields(state, reasons, skipped):
    with pytest.raises(ValueError):
        values().ActualBindingAssessment(state, reasons, skipped)
