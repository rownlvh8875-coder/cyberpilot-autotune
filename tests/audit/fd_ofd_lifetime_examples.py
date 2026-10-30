"""Hand specified SYNTHETIC examples, not kernel/guest observations."""

import copy
from typing import Any

from .fd_ofd_lifetime_model import context_digest

T, U, P, C, OFD, PIN = [1, 0], [2, 0], [1, 0], [2, 0], [1, 0], [1, 0]
OBJECT = "a" * 64


def frame(rows: list[tuple[str, list[Any]]]) -> dict[str, Any]:
    context = {
        "session_id": "synthetic-session",
        "boot_scope": "synthetic-boot",
        "source_revision": "3a831fdd423aa98638082eba126519db19f432d6",
        "source_digest": "b" * 64,
        "scope_digest": "c" * 64,
        "profile": "PROPOSED_KERNEL_SERIALIZED_LIFETIME_V1",
        "clock_domain": "SYNTHETIC_KERNEL_MONOTONIC_NS",
        "cpus": [0, 1],
    }
    events = [
        {
            "seq": i,
            "time_ns": i * 10,
            "cpu": 0,
            "cpu_seq": i,
            "context_digest": context_digest(context),
            "kind": kind,
            "data": copy.deepcopy(values),
        }
        for i, (kind, values) in enumerate(rows, 1)
    ]
    return {
        "schema": "fd-ofd-lifetime-design-v1",
        "evidence_class": "SYNTHETIC_ONLY",
        "context": context,
        "events": events,
        "coverage": {
            "start_fence": 0,
            "end_fence": len(events) + 1,
            "cpus": [
                {
                    "cpu": cpu,
                    "armed": True,
                    "drained": True,
                    "emitted": len(events) if cpu == 0 else 0,
                    "last_source_seq": len(events) if cpu == 0 else 0,
                    "dropped": 0,
                }
                for cpu in (0, 1)
            ],
        },
    }


def prefix() -> list[tuple[str, list[Any]]]:
    return [
        ("TABLE_NEW", [T]),
        ("TASK_START", [P, T]),
        ("INVENTORY", [P, 0, T, 0, []]),
        ("OFD_NEW", [P, 0, OFD, OBJECT]),
        ("INSTALL", [P, T, 0, 0, 0, OFD, False]),
        ("PIN", [PIN, OFD]),
        ("DUP", [P, T, 1, 0, 0, 3, 0, "DUP3", True]),
        ("INVENTORY", [P, 0, T, 2, [[0, 0, OFD, False], [3, 0, OFD, True]]]),
    ]


def tail() -> list[tuple[str, list[Any]]]:
    return [
        ("EXEC", [P, T, 2, T, 0, 1, [[3, 0, OFD, True]]]),
        ("INVENTORY", [P, 1, T, 3, [[0, 0, OFD, False]]]),
        ("CLOSE", [P, T, 3, 0, 0, OFD]),
        ("DETACH", [P, 1, T, 4]),
        ("TABLE_FREE", [T, 4, []]),
        ("REAP", [P, 1]),
        ("UNPIN", [PIN, OFD]),
        ("OFD_FREE", [OFD]),
    ]


def complete(scenario: str = "basic") -> dict[str, Any]:
    pre = prefix()
    after = tail()
    counts = [1, 1, 1, 1]
    if scenario == "basic":
        rows = pre + after
    elif scenario == "share":
        rows = pre + [
            ("FORK", [P, T, 2, C, T, True]),
            ("INVENTORY", [C, 0, T, 2, [[0, 0, OFD, False], [3, 0, OFD, True]]]),
            ("CLOSE", [C, T, 2, 0, 0, OFD]),
            ("INVENTORY", [P, 0, T, 3, [[3, 0, OFD, True]]]),
            ("DETACH", [C, 0, T, 3]),
            ("REAP", [C, 0]),
            ("CLOSE", [P, T, 3, 3, 0, OFD]),
            ("DETACH", [P, 0, T, 4]),
            ("TABLE_FREE", [T, 4, []]),
            ("REAP", [P, 0]),
            ("UNPIN", [PIN, OFD]),
            ("OFD_FREE", [OFD]),
        ]
        counts = [2, 1, 1, 1]
    elif scenario in ("fork", "unshare", "exec_copy"):
        shared = scenario != "fork"
        child_table = T if shared else U
        rows = pre + [
            ("FORK", [P, T, 2, C, child_table, shared]),
            (
                "INVENTORY",
                [C, 0, child_table, 2 if shared else 0, [[0, 0, OFD, False], [3, 0, OFD, True]]],
            ),
        ]
        if scenario == "unshare":
            rows += [
                ("UNSHARE", [C, T, 2, U]),
                ("INVENTORY", [C, 0, U, 0, [[0, 0, OFD, False], [3, 0, OFD, True]]]),
            ]
        if scenario == "fork":
            rows += [
                ("CLOSE", [C, U, 0, 0, 0, OFD]),
                ("DETACH", [C, 0, U, 1]),
                ("TABLE_FREE", [U, 1, [[3, 0, OFD, True]]]),
                ("REAP", [C, 0]),
            ]
        else:
            rows += [
                (
                    "EXEC",
                    [
                        C,
                        T if scenario == "exec_copy" else U,
                        2 if scenario == "exec_copy" else 0,
                        U,
                        0,
                        1,
                        [[3, 0, OFD, True]],
                    ],
                ),
                ("INVENTORY", [C, 1, U, 1, [[0, 0, OFD, False]]]),
                ("DETACH", [C, 1, U, 1]),
                ("TABLE_FREE", [U, 1, [[0, 0, OFD, False]]]),
                ("REAP", [C, 1]),
            ]
        rows += after
        counts = [2, 2, 1, 1]
    elif scenario == "unshare_same":
        rows = (
            pre
            + [
                ("UNSHARE", [P, T, 2, T]),
                ("INVENTORY", [P, 0, T, 2, [[0, 0, OFD, False], [3, 0, OFD, True]]]),
            ]
            + after
        )
    elif scenario == "reuse":
        newer = [1, 1]
        rows = pre[:6] + [
            ("CLOSE", [P, T, 1, 0, 0, OFD]),
            ("UNPIN", [PIN, OFD]),
            ("OFD_FREE", [OFD]),
            ("OFD_NEW", [P, 0, newer, OBJECT]),
            ("INSTALL", [P, T, 2, 0, 1, newer, False]),
            ("CLOSE", [P, T, 3, 0, 1, newer]),
            ("DETACH", [P, 0, T, 4]),
            ("TABLE_FREE", [T, 4, []]),
            ("REAP", [P, 0]),
            ("OFD_FREE", [newer]),
        ]
        counts = [1, 1, 2, 1]
    else:
        raise ValueError("unknown synthetic scenario")
    return frame(rows + [("END", counts)])


def additional(scenario: str) -> dict[str, Any]:
    """Additional hand-checked semantic deltas; no observations or inferred authority."""
    pre = prefix()
    counts = [1, 1, 1, 1]
    if scenario == "cloexec":
        rows = pre + [
            ("CLOEXEC", [P, T, 2, 0, 0, False, True]),
            ("INVENTORY", [P, 0, T, 3, [[0, 0, OFD, True], [3, 0, OFD, True]]]),
            ("EXEC", [P, T, 3, T, 0, 1, [[0, 0, OFD, True], [3, 0, OFD, True]]]),
            ("INVENTORY", [P, 1, T, 4, []]),
            ("DETACH", [P, 1, T, 4]),
            ("TABLE_FREE", [T, 4, []]),
            ("REAP", [P, 1]),
            ("UNPIN", [PIN, OFD]),
            ("OFD_FREE", [OFD]),
        ]
    elif scenario == "empty_exec":
        rows = pre[:6] + [
            ("EXEC", [P, T, 1, T, 0, 1, []]),
            ("INVENTORY", [P, 1, T, 1, [[0, 0, OFD, False]]]),
            ("CLOSE", [P, T, 1, 0, 0, OFD]),
            ("DETACH", [P, 1, T, 2]),
            ("TABLE_FREE", [T, 2, []]),
            ("REAP", [P, 1]),
            ("UNPIN", [PIN, OFD]),
            ("OFD_FREE", [OFD]),
        ]
    elif scenario == "dup_replace":
        rows = pre + [
            ("DUP", [P, T, 2, 0, 0, 3, 1, "DUP2", False]),
            ("EXEC", [P, T, 3, T, 0, 1, []]),
            ("INVENTORY", [P, 1, T, 3, [[0, 0, OFD, False], [3, 1, OFD, False]]]),
            ("CLOSE", [P, T, 3, 0, 0, OFD]),
            ("CLOSE", [P, T, 4, 3, 1, OFD]),
            ("DETACH", [P, 1, T, 5]),
            ("TABLE_FREE", [T, 5, []]),
            ("REAP", [P, 1]),
            ("UNPIN", [PIN, OFD]),
            ("OFD_FREE", [OFD]),
        ]
    elif scenario == "distinct_ofds":
        rows = (
            pre[:6]
            + [("OFD_NEW", [P, 0, [2, 0], OBJECT]), ("OFD_FREE", [[2, 0]])]
            + pre[6:]
            + tail()
        )
        counts = [1, 1, 2, 1]
    elif scenario == "table_task_reuse":
        rows = (
            pre
            + [
                ("FORK", [P, T, 2, C, U, False]),
                ("INVENTORY", [C, 0, U, 0, [[0, 0, OFD, False], [3, 0, OFD, True]]]),
                ("DETACH", [C, 0, U, 0]),
                ("TABLE_FREE", [U, 0, [[0, 0, OFD, False], [3, 0, OFD, True]]]),
                ("REAP", [C, 0]),
                ("FORK", [P, T, 2, [2, 1], [2, 1], False]),
                ("INVENTORY", [[2, 1], 0, [2, 1], 0, [[0, 0, OFD, False], [3, 0, OFD, True]]]),
                ("DETACH", [[2, 1], 0, [2, 1], 0]),
                ("TABLE_FREE", [[2, 1], 0, [[0, 0, OFD, False], [3, 0, OFD, True]]]),
                ("REAP", [[2, 1], 0]),
            ]
            + tail()
        )
        counts = [3, 3, 1, 1]
    else:
        raise ValueError("unknown additional synthetic scenario")
    return frame(rows + [("END", counts)])


def catalog() -> list[dict[str, Any]]:
    scenarios = ("basic", "share", "fork", "unshare", "exec_copy", "unshare_same", "reuse")
    extras = ("cloexec", "empty_exec", "dup_replace", "distinct_ofds", "table_task_reuse")
    out: list[dict[str, Any]] = []

    def add(name: str, graph: dict[str, Any], expected: bool) -> None:
        out.append(
            {
                "case_id": f"L{len(out) + 1:03d}",
                "name": name,
                "expected_consistent": expected,
                "graph": graph,
            }
        )

    for name in scenarios:
        add(name, complete(name), True)
    for name in extras:
        add(name, additional(name), True)
    mutations: tuple[tuple[str, str, str, Any], ...] = (
        ("observed_relabel", "basic", "class", None),
        ("first_slot_guessed", "basic", "INSTALL", (4, 1)),
        ("bool_fd_not_zero", "basic", "INSTALL", (3, False)),
        ("missing_fd_not_zero", "basic", "INSTALL", (3, None)),
        ("float_fd_not_zero", "basic", "INSTALL", (3, 0.0)),
        ("stale_table_epoch", "basic", "DUP", (2, 0)),
        ("stale_source_slot", "basic", "DUP", (4, 1)),
        ("dup2_retains_cloexec", "basic", "DUP", (7, "DUP2")),
        ("dup_self_not_delta", "basic", "DUP", (5, 0)),
        ("copy_guesses_same_table", "fork", "FORK", (4, T)),
        ("share_guesses_new_table", "share", "FORK", (4, U)),
        ("exec_mutates_shared_table", "exec_copy", "EXEC", (3, T)),
        ("exec_ordinal_skipped", "basic", "EXEC", (5, 2)),
        ("exec_missing_close_delta", "basic", "EXEC", (6, [])),
        ("wrong_ofd_in_close", "basic", "CLOSE", (5, [2, 0])),
        ("missing_snapshot", "basic", "INVENTORY", (4, None)),
        ("wrong_table_at_detach", "basic", "DETACH", (2, U)),
        ("wrong_exec_at_reap", "basic", "REAP", (1, 0)),
        ("wrong_teardown_epoch", "basic", "TABLE_FREE", (1, 0)),
        ("unknown_effect", "basic", "unknown", None),
        ("source_context_splice", "basic", "splice", None),
        ("per_cpu_gap", "basic", "cpu_gap", None),
        ("global_sequence_gap", "basic", "global_gap", None),
        ("loss_known", "basic", "loss", 1),
        ("loss_unknown", "basic", "loss", None),
        ("missing_cpu", "basic", "cpu_missing", None),
        ("cpu_not_drained", "basic", "drain", False),
        ("source_watermark_drift", "basic", "watermark", 0),
    )
    for name, scenario, kind, change in mutations:
        graph = complete(scenario)
        if kind in {
            "class",
            "unknown",
            "splice",
            "cpu_gap",
            "global_gap",
            "loss",
            "cpu_missing",
            "drain",
            "watermark",
        }:
            if kind == "class":
                graph["evidence_class"] = "OBSERVED"
            elif kind == "unknown":
                graph["events"][3]["kind"] = "IO_URING_UNCOVERED"
            elif kind == "splice":
                graph["events"][3]["context_digest"] = "f" * 64
            elif kind == "cpu_gap":
                graph["events"][3]["cpu_seq"] = 99
            elif kind == "global_gap":
                graph["events"][3]["seq"] = 99
            elif kind == "loss":
                graph["coverage"]["cpus"][0]["dropped"] = change
            elif kind == "cpu_missing":
                graph["coverage"]["cpus"].pop()
            elif kind == "drain":
                graph["coverage"]["cpus"][1]["drained"] = change
            else:
                graph["coverage"]["cpus"][0]["last_source_seq"] = change
        else:
            event = next(e for e in graph["events"] if e["kind"] == kind)
            assert change is not None
            event["data"][change[0]] = change[1]
        add(name, graph, False)
    for name, a, b in (
        ("ofd_free_before_unpin", "OFD_FREE", "UNPIN"),
        ("table_free_before_detach", "TABLE_FREE", "DETACH"),
        ("reap_before_detach", "REAP", "DETACH"),
    ):
        graph = complete()
        rows = [(e["kind"], e["data"]) for e in graph["events"]]
        at = next(i for i, r in enumerate(rows) if r[0] == a)
        item = rows.pop(at)
        rows.insert(next(i for i, r in enumerate(rows) if r[0] == b), item)
        add(name, frame(rows), False)
    return out
