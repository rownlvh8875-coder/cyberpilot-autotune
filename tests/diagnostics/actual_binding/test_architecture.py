"""AST and real-call boundary checks, not a native containment certification."""

import ast
import inspect
import json
import sys
from pathlib import Path

import pytest

from cyberpilot_autotune.diagnostics import actual_binding
from cyberpilot_autotune.diagnostics.actual_binding import assess_actual_binding
from tests.diagnostics.actual_binding.actual_binding_test_vectors import complete_vector


def test_public_surface_has_no_reader_or_factory():
    assert set(actual_binding.__all__) == {
        "ActualDiagnosticBundle",
        "PrelaunchExpectedReference",
        "CaptureFreezeExpectedReference",
        "ActualBindingAssessment",
        "assess_actual_binding",
    }
    assert tuple(inspect.signature(assess_actual_binding).parameters) == (
        "bundle",
        "expected_pre",
        "expected_post",
    )


def test_no_raw_parser_or_old_api_dependency():
    permitted = {"dataclasses", "hashlib", "json", "re", "typing"}
    forbidden_calls = {
        "open",
        "eval",
        "exec",
        "__import__",
        "input",
        "compile",
        "write_text",
        "write_bytes",
        "read_text",
        "read_bytes",
        "connect",
        "Popen",
        "start_new_thread",
        "monotonic_ns",
        "time",
        "sleep",
    }
    root = Path(actual_binding.__file__).parent
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(n.name.split(".")[0] in permitted for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 1 or node.module.split(".")[0] in permitted
            elif isinstance(node, ast.Call):
                function = node.func
                name = (
                    function.id
                    if isinstance(function, ast.Name)
                    else (function.attr if isinstance(function, ast.Attribute) else None)
                )
                assert name not in forbidden_calls


def test_only_six_contract_documents_parsed_not_raw_json():
    v = complete_vector()
    calls = []

    def profile(frame, event, arg):
        if event == "call" and frame.f_code is json.loads.__code__:
            calls.append(1)

    sys.setprofile(profile)
    try:
        r = assess_actual_binding(v.bundle, expected_pre=v.pre, expected_post=v.post)
    finally:
        sys.setprofile(None)
    assert len(calls) == 6 and r.content_status == "NOT_EVALUATED"


def test_fixed_negative_provenance_with_fake_receipts():
    v = complete_vector()
    r = assess_actual_binding(v.bundle, expected_pre=v.pre, expected_post=v.post)
    assert r.provenance == "BLOCKED_NO_INDEPENDENT_VERIFICATION"
    for kw in ("reader", "writer", "clock", "grant", "factory", "uri", "retention_receipt"):
        with pytest.raises(TypeError):
            assess_actual_binding(
                v.bundle, expected_pre=v.pre, expected_post=v.post, **{kw: object()}
            )
