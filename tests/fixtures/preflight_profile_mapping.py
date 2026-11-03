"""Explicitly fictional S0 source input; never observed R0 or H execution."""

import json
from pathlib import Path

S0 = "SYNTHETIC_MAPPING_S0"


def registration():
    root = Path(__file__).resolve().parents[2]
    return json.loads(
        (
            root
            / "docs/evidence/audit_compatibility/preflight-profile-mapping-v1/registration.json"
        ).read_text()
    )


def source_bytes():
    return registration()["acceptance"]["fixture"]["canonical_source_utf8"].encode()


def source_document():
    return json.loads(source_bytes())


def binding_fields():
    return registration()["acceptance"]["baseline_binding"].copy()


def encoded(document):
    return (
        json.dumps(
            document, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
        + "\n"
    ).encode()
