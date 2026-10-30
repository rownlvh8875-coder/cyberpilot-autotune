"""Literal synthetic protocol data, never actual build/seal/approval evidence."""

import importlib


def models():
    assert importlib.util.find_spec("compatibility.guest_build_receipt") is not None
    return importlib.import_module("compatibility.guest_build_receipt.models")


SHA_A = "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"
SHA_B = "3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d"
EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def identity():
    m = models()
    return m.BuildIdentity(
        "session-1",
        "attempt-1",
        "1" * 64,
        "2" * 64,
        "3" * 64,
        "4" * 64,
        "5" * 64,
        "GUEST_TRACER_OBSERVATION_MONOTONIC_NS",
    )


def build():
    m = models()
    codec = importlib.import_module("compatibility.guest_build_receipt.codec")
    context = identity()
    digest = codec.receipt_digest(context)
    materials = (
        m.BuildMaterial(
            "compiler", 0, m.MaterialRole.TOOLCHAIN, "toolchain/cc", 1, SHA_A, "2" * 64
        ),
        m.BuildMaterial("source", 0, m.MaterialRole.SOURCE, "src/a.c", 1, SHA_A, "1" * 64),
    )
    images = (m.TaskImage(1, 0, None, "compiler", 0, 10, 100),)
    uses = (
        m.InputUse(1, digest, 1, 0, "compiler", 0, m.UseKind.EXEC_BOUND, 11, None, None, None),
        m.InputUse(2, digest, 1, 0, "source", 0, m.UseKind.READ_BYTES, 20, 0, 1, SHA_A),
        m.InputUse(3, digest, 1, 0, "source", 0, m.UseKind.METADATA_ONLY, 21, None, None, None),
        m.InputUse(4, digest, 1, 0, "source", 0, m.UseKind.MMAP_BOUND, 22, 0, 4096, None),
    )
    outputs = (m.BuildOutput("object", 0, "out/a.o", 1, SHA_B, 90, 1, 0),)
    completion = m.BuildCompletion(
        m.ExitKind.EXITED, 0, None, True, 0, "6" * 64, "7" * 64, "8" * 64, "9" * 64
    )
    return m.BuildReceipt(
        context, materials, images, uses, outputs, 10, 100, completion, m.EvidenceKind.SYNTHETIC
    )


def promotion(receipt=None):
    m = models()
    codec = importlib.import_module("compatibility.guest_build_receipt.codec")
    receipt = build() if receipt is None else receipt
    return m.PromotionReceipt(
        codec.receipt_digest(receipt.identity),
        codec.receipt_digest(receipt),
        "object",
        0,
        SHA_B,
        SHA_B,
        SHA_B,
        "a" * 64,
        "b" * 64,
        101,
        102,
        103,
        104,
        "c" * 64,
        "d" * 64,
        "e" * 64,
    )
