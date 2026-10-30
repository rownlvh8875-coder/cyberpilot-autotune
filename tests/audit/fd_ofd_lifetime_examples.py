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
