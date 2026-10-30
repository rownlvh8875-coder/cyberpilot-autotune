"""No request may turn the outer host into the kernel-policy test target."""

import importlib

import pytest


def api():
    assert (
        importlib.util.find_spec("compatibility.containment_backend_harmless.host_main") is not None
    )
    return importlib.import_module("compatibility.containment_backend_harmless.host_main")


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--fixture", "HF01"],
        ["--execute-host"],
        ["--command", "mount"],
        ["--kernel", "/boot/kernel"],
        ["--execute-guest", "--fixture", "HF25"],
        ["--execute-guest", "--fixture", "HF01", "--vm-root", "/"],
    ],
)
def test_entrypoint_without_fixed_guest_scope_rejects_before_io(argv, monkeypatch):
    module = api()

    def no_execution(*args, **kwargs):
        pytest.fail("invalid/default invocation must not execute or inspect host policy")

    monkeypatch.setattr(module, "execute_guest", no_execution)
    assert module.main(argv) == 2


def test_parser_requires_explicit_fixture_not_implicit_all():
    assert api().main(["--execute-guest"]) == 2


def test_known_request_is_data_only_until_explicit_dispatch(monkeypatch):
    module = api()
    seen = []
    monkeypatch.setattr(module, "execute_guest", lambda selected: seen.append(selected) or 0)
    assert module.main(["--execute-guest", "--fixture", "HF01", "--fixture", "HF24"]) == 0
    assert seen == [("HF01", "HF24")]


def test_duplicate_fixture_request_rejects_instead_of_changing_execution_count():
    assert api().main(["--execute-guest", "--fixture", "HF01", "--fixture", "HF01"]) == 2
