"""Hand-authored trace examples, NOT actual kernel or trusted evidence."""

import json


def simple_events():
    return [
        ("BIRTH", 1, 101, 0, [0, 0]),
        ("FDS", 1, 101, 0, [0, 1, 0, 0, 1, 10, 0o010600, 7]),
        ("ENTER", 1, 101, 0, [1, 0xC000003E, 257, 2**64 - 100, 0x8000, 0, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [1, 3]),
        ("FDS", 1, 101, 0, [1, 2, 0, 0, 1, 10, 0o010600, 7, 3, 0x80000, 1, 20, 0o100444, 7]),
        ("ENTER", 1, 101, 0, [2, 0xC000003E, 3, 3, 0, 0, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [2, 0]),
        ("FDS", 1, 101, 0, [2, 1, 0, 0, 1, 10, 0o010600, 7]),
        ("ENTER", 1, 101, 0, [3, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 0, [0]),
        ("ABORT", 1, 101, 0, [3, 0]),
        ("EXIT", 1, 101, 0, [0]),
    ]


def wire(events=None, *, tasks=1, live=0, root_status=0):
    source = simple_events() if events is None else events
    records = [
        {
            "kind": k,
            "seq": i,
            "mono_ns": 100 + i,
            "task": t,
            "tid": pid,
            "image": image,
            "values": v,
        }
        for i, (k, t, pid, image, v) in enumerate(source, 1)
    ]
    return "\n".join(
        [
            'TRACE_BEGIN {"version":"guest-syscall-fd-v1","fixture_id":"HF01",'
            '"clock_domain":"GUEST_TRACER_OBSERVATION_MONOTONIC_NS"}',
            *["TRACE_EVENT " + json.dumps(record) for record in records],
            "TRACE_END "
            + json.dumps(
                {"events": len(records), "tasks": tasks, "live": live, "root_status": root_status}
            ),
        ]
    )


def donation_events():
    # Parent101 is the fixed broker; child102 is the requesting tracee.
    base = [0, 0, 1, 10, 0o010600, 7, 4, 0x80000, 2, 30, 0o100600, 7]
    opened = base + [6, 0x80000, 1, 20, 0o100444, 7]
    target = [
        0,
        0,
        1,
        10,
        0o010600,
        7,
        1,
        0x80000,
        1,
        20,
        0o100444,
        7,
        4,
        0x80000,
        2,
        30,
        0o100600,
        7,
    ]
    return [
        ("BIRTH", 1, 101, 0, [0, 0]),
        ("FDS", 1, 101, 0, [0, 2, *base]),
        ("ENTER", 1, 101, 0, [1, 0xC000003E, 56, 17, 0, 0, 0, 0, 0]),
        ("BIRTH", 2, 102, 0, [1, 17]),
        ("FDS", 2, 102, 0, [0, 2, *base]),
        ("RETURN", 1, 101, 0, [1, 102]),
        ("ENTER", 2, 102, 0, [2, 0xC000003E, 257, 2**64 - 100, 0x8000, 0, 0, 0, 0]),
        ("ENTER", 1, 101, 0, [3, 0xC000003E, 16, 4, 0xC0502100, 0xA000, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [3, 0]),
        (
            "NOTIFY_RECV",
            1,
            101,
            0,
            [3, 77, 102, 0, 257, 0xC000003E, 4, 2**64 - 100, 0x8000, 0, 0, 0, 0],
        ),
        ("ENTER", 1, 101, 0, [4, 0xC000003E, 257, 2**64 - 100, 0x9000, 0x80000, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [4, 6]),
        ("FDS", 1, 101, 0, [4, 3, *opened]),
        ("ENTER", 1, 101, 0, [5, 0xC000003E, 16, 4, 0x40182103, 0xB000, 0, 0, 0]),
        ("RETURN", 1, 101, 0, [5, 1]),
        ("ADDFD", 1, 101, 0, [5, 77, 2, 6, 0, 0x80000, 1]),
        ("RETURN", 2, 102, 0, [2, 1]),
        ("FDS", 2, 102, 0, [2, 3, *target]),
        ("ENTER", 2, 102, 0, [6, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 2, 102, 0, [0]),
        ("ABORT", 2, 102, 0, [6, 0]),
        ("EXIT", 2, 102, 0, [0]),
        ("ENTER", 1, 101, 0, [7, 0xC000003E, 231, 0, 0, 0, 0, 0, 0]),
        ("PRE_EXIT", 1, 101, 0, [0]),
        ("ABORT", 1, 101, 0, [7, 0]),
        ("EXIT", 1, 101, 0, [0]),
    ]
