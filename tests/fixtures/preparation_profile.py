"""Synthetic claims, not proposed H budgets or actual execution receipts."""

import json
from pathlib import Path

from tests.audit_preparation_profile import decode_policy, decode_profile


def registration():
    root = Path(__file__).resolve().parents[2]
    return json.loads(
        (
            root / "docs/evidence/audit_compatibility/preparation-profile-v1/registration.json"
        ).read_text()
    )


def complete():
    vector = registration()["conformance"]
    return (
        decode_profile(vector["canonical_record_utf8"].encode()),
        decode_policy(vector["canonical_policy_utf8"].encode()),
    )
