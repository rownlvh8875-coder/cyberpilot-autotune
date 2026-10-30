"""Independent I1/I2/I3: exact physical frames and causal capture phases."""

from dataclasses import replace

import pytest

from tests.fixtures.guest_consumption import PROGRAM_SHA, module, profile, rows, text


def numbered(r):
    return [dict(row, seq=i, time_ns=i + 10) for i, row in enumerate(r, 1)]


def produce(r, p=None):
    return module("producer").produce_receipt(
        module("wire").parse_capture(text(numbered(r))), profile() if p is None else p
    )


@pytest.mark.parametrize(
    "separator", ["\v", "\f", "\r", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"]
)
def test_interleaved_physical_line_cannot_be_repaired_by_nonprotocol_separator(separator):
    raw = text().replace("CONSUMPTION ", "[console interleave]" + separator + "CONSUMPTION ", 1)
    with pytest.raises(ValueError):
        module("wire").parse_capture(raw)


def test_declared_lf_and_crlf_frames_remain_accepted_without_payload_repair():
    w = module("wire")
    lf = w.parse_capture("boot console\n" + text())
    crlf = w.parse_capture("boot console\r\n" + text().replace("\n", "\r\n"))
    assert w.capture_digest(lf) == w.capture_digest(crlf)
    assert module("producer").produce_receipt(crlf, profile()).trace_window_complete


@pytest.mark.parametrize("same_bytes", [True, False])
def test_fork_cannot_change_the_parent_image_object_even_for_identical_bytes(same_bytes):
    from compatibility.guest_build_receipt.models import MaterialRole

    r = rows()
    other_sha = (
        PROGRAM_SHA
        if same_bytes
        else "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d"
    )
    p = profile()
    if not same_bytes:
        c = module("contracts")
        p = replace(
            p,
            materials=(
                *p.materials,
                c.KnownMaterial("other", MaterialRole.TOOLCHAIN, "other-probe", 1, other_sha),
            ),
        )
    obj = dict(r[1], values=[3, 1, 103, 1, other_sha])
    child = dict(r[2], task=2, values=[1, 3])
    exit_child = dict(r[-2], task=2, image=0)
    r = [*r[:5], obj, child, exit_child, *r[5:]]
    r[-1]["values"] = [True, 2, 3, 0]
    with pytest.raises(ValueError):
        produce(r, p)


def test_fork_inherits_exact_object_and_may_change_only_via_later_exec():
    from compatibility.guest_build_receipt.models import MaterialRole

    r = rows()
    other_sha = "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d"
    c = module("contracts")
    p = profile()
    p = replace(
        p,
        materials=(
            *p.materials,
            c.KnownMaterial("other", MaterialRole.TOOLCHAIN, "other-probe", 1, other_sha),
        ),
    )
    obj = dict(r[1], values=[3, 1, 103, 1, other_sha])
    child = dict(r[2], task=2, values=[1, 1])
    executed = dict(r[3], task=2, image=1, values=[3])
    exit_child = dict(r[-2], task=2, image=1)
    r = [*r[:5], obj, child, executed, exit_child, *r[5:]]
    r[-1]["values"] = [True, 2, 3, 0]
    o = produce(r, p)
    child_images = [i for i in o.receipt.images if i.task_generation == 2]
    assert [(i.exec_generation, i.image_id) for i in child_images] == [
        (0, "program-1"),
        (1, "other-3"),
    ]


@pytest.mark.parametrize(
    "kind", ["READ", "MAP", "META", "EXEC", "BIRTH", "OBJECT", "FAILED", "ERROR"]
)
def test_fatal_error_disallows_new_observations_in_the_abort_phase(kind):
    r = rows()
    if kind in ("FAILED", "ERROR"):
        index = len(r) - 2
        values = [0, -14] if kind == "FAILED" else ["RETURNED_BUFFER_UNAVAILABLE"]
        r.insert(index, dict(r[5], kind=kind, values=values))
    else:
        index = next(i for i, row in enumerate(r) if row["kind"] == kind)
    current_image = 0 if index <= 3 else 1
    task = 0 if index <= 2 else 1
    error = dict(
        r[0],
        kind="ERROR",
        task=task,
        image=0 if task == 0 else current_image,
        values=["RETURNED_BUFFER_UNAVAILABLE"],
    )
    r.insert(index, error)
    r[-1]["values"][0] = False
    with pytest.raises(ValueError):
        produce(r)


def test_abort_still_allows_original_payload_draining_and_actual_signal_reap():
    r = rows()
    error = dict(r[5], kind="ERROR", values=["RETURNED_BUFFER_UNAVAILABLE"])
    payload = dict(r[0], kind="PAYLOAD", values=["616263"])
    r = [
        *r[:-2],
        error,
        payload,
        dict(r[-2], values=["SIGNALLED", 9]),
        dict(r[-1], values=[False, 1, 2, 0]),
    ]
    o = produce(r)
    assert not o.trace_window_complete and o.receipt.completion.term_signal == 9
    assert "RETURNED_BUFFER_UNAVAILABLE" in o.profile_reasons
    assert len(o.receipt.uses) == 7
