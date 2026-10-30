"""Literal synthetic wire examples, not actual-capture evidence."""

import hashlib
import importlib
import json

INPUT = b"0123456789ABCDEF\n"
PROGRAM_SHA = "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"
CLOCK = "GUEST_TRACER_OBSERVATION_MONOTONIC_NS"


def module(name):
    assert importlib.util.find_spec("compatibility.guest_consumption") is not None
    assert importlib.util.find_spec("compatibility.guest_consumption." + name) is not None
    return importlib.import_module("compatibility.guest_consumption." + name)


def rows():
    values = [
        ("BEGIN", 0, 0, ["guest-consumption-prototype-v1", "CP01", CLOCK]),
        ("OBJECT", 0, 0, [1, 1, 101, 1, PROGRAM_SHA]),
        ("BIRTH", 1, 0, [None, 1]),
        ("EXEC", 1, 1, [1]),
        ("OBJECT", 0, 0, [2, 1, 102, len(INPUT), hashlib.sha256(INPUT).hexdigest()]),
        ("READ", 1, 1, [2, 0, 4, "30313233"]),
        ("READ", 1, 1, [2, 4, 4, "34353637"]),
        ("READ", 1, 1, [2, 8, 3, "383941"]),
        ("READ", 1, 1, [2, 100, 0, ""]),
        ("MAP", 1, 1, [2, 0, 4096]),
        ("META", 1, 1, [2]),
        ("EXIT", 1, 1, ["EXITED", 0]),
        ("END", 0, 0, [True, 1, 2, 0]),
    ]
    return [
        dict(seq=i, time_ns=10 + i, kind=kind, task=task, image=image, values=v)
        for i, (kind, task, image, v) in enumerate(values, 1)
    ]


def text(values=None):
    return (
        "\n".join(
            "CONSUMPTION " + json.dumps(r, separators=(",", ":"))
            for r in (rows() if values is None else values)
        )
        + "\n"
    )


def profile():
    from compatibility.guest_build_receipt.models import BuildIdentity, MaterialRole

    c = module("contracts")
    return c.ConsumptionProfile(
        BuildIdentity(
            "fixture-session", "CP01", "1" * 64, "2" * 64, "3" * 64, "4" * 64, "5" * 64, CLOCK
        ),
        (
            c.KnownMaterial("program", MaterialRole.TOOLCHAIN, "consumption-probe", 1, PROGRAM_SHA),
            c.KnownMaterial(
                "input",
                MaterialRole.SOURCE,
                "input/sample.bin",
                len(INPUT),
                hashlib.sha256(INPUT).hexdigest(),
            ),
        ),
    )
