import dataclasses
import inspect

import pytest


def test_internal_domain_public_api_is_closed():
    from native_e_lab.domain import DomainObservation, run_domain_lab

    assert not inspect.signature(run_domain_lab).parameters
    for key in ("unit", "pid", "fd", "path", "command", "receipt"):
        with pytest.raises(TypeError):
            run_domain_lab(**{key: "untrusted"})
    receipt = DomainObservation("UNAVAILABLE", "UNKNOWN", None, None, ())
    assert not any(receipt.flags.values())
    assert receipt.provider_registration == "UNBOUND"
    assert not any(hasattr(receipt, x) for x in ("stop", "resume", "recover", "close"))
    assert dataclasses.asdict(receipt)["domain"] is None


@pytest.mark.parametrize("mask", [0, 1, 127, 254, 256, 511])
def test_incomplete_or_extra_domain_claim_is_rejected(mask):
    import struct

    from native_e_lab.domain import _domain_report
    from native_e_lab.protocol import Context, ProtocolError, Stage

    ctx = Context.fresh()
    raw = ctx.message(Stage.COMPLETE, 4) + struct.pack("!I", mask)
    with pytest.raises(ProtocolError):
        _domain_report(ctx, raw)


def test_domain_report_requires_observed_context_and_all_fields():
    import struct

    from native_e_lab.domain import _domain_report
    from native_e_lab.protocol import Context, ProtocolError, Stage

    ctx = Context.fresh()
    raw = ctx.message(Stage.COMPLETE, 4) + struct.pack("!I", 255)
    report = _domain_report(ctx, raw)
    assert all(report.values())
    with pytest.raises(ProtocolError):
        _domain_report(Context.fresh(), raw)
