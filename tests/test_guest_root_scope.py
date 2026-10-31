"""Detect invented root birth, inherited identities, wrong roles and lost provenance."""

import importlib
import importlib.util
from dataclasses import FrozenInstanceError

import pytest

ALLOC = "seq=1 kind=TASK_ALLOC scope=1 actor=0 task=1 table=0 ofd=0 old=0 fd=-1 flags=-1 mono=10"
TABLE = "seq=2 kind=TABLE_NEW scope=1 actor=0 task=1 table=2 ofd=0 old=0 fd=-1 flags=-1 mono=11"
COMMIT = "seq=3 kind=TASK_COMMIT scope=1 actor=0 task=1 table=2 ofd=0 old=0 fd=-1 flags=-1 mono=12"


def wire(events=(ALLOC, TABLE, COMMIT), *, case="NORMAL", attempted=3, failed=0):
    n = len(events)
    capacity = 2 if case == "SMALL_BUFFER" else 128
    return (
        "CPS_DRIVER ok=1 root=0 child=0\n"
        f"CPS_META version=1 case={case} release=6.12.113-cpscope-v1 "
        f"cpus=1 capacity={capacity} root=1\n"
        f"CPS_COUNT attempted={attempted} reserved={n} committed={n} "
        f"failed={failed} discarded=0 pending=0\n"
        + "".join("CPS_EVENT " + e + "\n" for e in events)
        + "CPS_END\nCPS_EXIT ok=1\n"
    ).encode()


def api():
    assert importlib.util.find_spec("tests.guest_root_scope.model") is not None, "missing scope API"
    return importlib.import_module("tests.guest_root_scope.model")


def test_three_source_stages_link_root_allocation_namespace_and_commit_without_armer_id():
    model = api()
    captured = model.parse_serial(wire())
    a, t, c = captured.events
    assert (a.task_id, a.actor_id, a.scope_id) == (1, None, 1)
    assert (t.task_id, t.table_id, t.old_id) == (1, 2, None)
    assert c.table_id == 2
    result = model.assess(captured)
    assert result.root_creation_observed and result.local_accounting_balanced
    assert not result.local_loss_observed
    assert result.reasons == ()
    assert result.status == "BLOCKED" and result.actual_global_drops is None
    assert len(result.permissions) == 9 and all(v is False for _, v in result.permissions)
    with pytest.raises(FrozenInstanceError):
        a.task_id = 123
    with pytest.raises(FrozenInstanceError):
        result.status = "QUALIFIED"


@pytest.mark.parametrize(
    ("events", "case", "attempted", "failed", "reason"),
    [
        ((TABLE, COMMIT), "ROOT_BIRTH_LOSS", 3, 1, "ROOT_CREATION_LINK_INCOMPLETE"),
        ((ALLOC, TABLE), "SMALL_BUFFER", 3, 1, "ROOT_CREATION_LINK_INCOMPLETE"),
        ((ALLOC, COMMIT), "NORMAL", 2, 0, "ROOT_CREATION_LINK_INCOMPLETE"),
        (
            (ALLOC, TABLE, COMMIT.replace("table=2", "table=9")),
            "NORMAL",
            3,
            0,
            "ROOT_CREATION_LINK_INCOMPLETE",
        ),
        (
            (ALLOC, TABLE, COMMIT.replace("actor=0", "actor=8")),
            "NORMAL",
            3,
            0,
            "ROOT_CREATION_LINK_INCOMPLETE",
        ),
        (
            (ALLOC, TABLE.replace("table=2", "table=1"), COMMIT.replace("table=2", "table=1")),
            "NORMAL",
            3,
            0,
            "SOURCE_COOKIE_COLLISION",
        ),
        (
            (ALLOC, TABLE, COMMIT, COMMIT.replace("seq=3", "seq=4")),
            "NORMAL",
            4,
            0,
            "DUPLICATE_CREATION_STAGE",
        ),
    ],
)
def test_missing_wrong_or_colliding_creation_records_never_prove_root(
    events, case, attempted, failed, reason
):
    model = api()
    decision = model.assess(
        model.parse_serial(wire(events, case=case, attempted=attempted, failed=failed))
    )
    assert not decision.root_creation_observed and reason in decision.reasons
    assert decision.local_accounting_balanced
    assert decision.local_loss_observed == (failed > 0)


@pytest.mark.parametrize(
    "change",
    [
        (b"version=1", b"version=2"),
        (b"cpus=1", b"cpus=2"),
        (b"scope=1 actor", b"scope=2 actor"),
        (b"task=1 table=0", b"task=0 table=0"),
        (b"fd=-1", b"fd=0"),
        (b"flags=-1", b"flags=0"),
        (b"seq=3", b"seq=2"),
        (b"actor=0", b"actor=01"),
        (b"mono=10", b"mono=18446744073709551616"),
        (b"CPS_EXIT ok=1", b"CPS_EXIT ok=0"),
        (b"kind=TASK_ALLOC", b"kind=UNKNOWN"),
        (b"root=1\n", b"root=0\n"),
        (b"CPS_END\n", b""),
    ],
)
def test_bad_wire_width_stage_scope_and_incomplete_completion_rejected(change):
    model = api()
    with pytest.raises(ValueError):
        model.parse_serial(wire().replace(*change))


def test_binding_fd_zero_and_cloexec_false_are_not_unavailable():
    model = api()
    event = "seq=4 kind=INSTALL scope=1 actor=1 task=0 table=2 ofd=3 old=0 fd=0 flags=0 mono=13"
    capture = model.parse_serial(wire((ALLOC, TABLE, COMMIT, event), attempted=4))
    assert capture.events[-1].fd == 0 and capture.events[-1].flags == 0
    assert capture.events[0].fd is None and capture.events[0].flags is None
    assert model.assess(capture).root_creation_observed


def test_descendant_actor_is_not_its_subject_or_inherited_task_cookie():
    model = api()
    descendant = (
        "seq=4 kind=TASK_ALLOC scope=1 actor=1 task=4 table=0 ofd=0 old=0 fd=-1 flags=-1 mono=13",
        "seq=5 kind=TABLE_NEW scope=1 actor=1 task=4 table=5 ofd=0 old=2 fd=-1 flags=-1 mono=14",
        "seq=6 kind=TASK_COMMIT scope=1 actor=1 task=4 table=5 ofd=0 old=0 fd=-1 flags=-1 mono=15",
    )
    good = model.parse_serial(wire((ALLOC, TABLE, COMMIT, *descendant), attempted=6))
    assert model.assess(good).root_creation_observed
    bad = wire((ALLOC, TABLE, COMMIT, *descendant), attempted=6).replace(b"task=4", b"task=1")
    assert not model.assess(model.parse_serial(bad)).root_creation_observed


def test_coherent_counts_are_not_global_losslessness_and_inconsistent_counts_are_visible():
    model = api()
    result = model.assess(model.parse_serial(wire(attempted=4)))
    assert not result.local_accounting_balanced
    assert "LOCAL_ACCOUNTING_OR_TRANSPORT_MISMATCH" in result.reasons
    assert result.actual_global_drops is None and result.status == "BLOCKED"


@pytest.mark.parametrize("raw", [b"", b"\xff", b"a" * 1048577, "not bytes", True])
def test_serial_input_bound_and_exact_bytes(raw):
    with pytest.raises(ValueError):
        api().parse_serial(raw)
