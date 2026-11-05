"""Offline review consistency lint. Never an installer, authorizer or resource executor."""

from __future__ import annotations

import configparser
import hashlib
import json
from pathlib import Path
from typing import Any

BASE = "8c0058ee8b24e7acd1de8bec248563d623ff60e4"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BLOCKERS = [
    "B01_PROTECTED_FACTORY_UNIMPLEMENTED",
    "B02_MANAGER_PRIVATE_FD_UNTESTED",
    "B03_ORIGINAL_P_FENCE_UNPROVEN",
    "B04_PRIVILEGED_BACKEND_UNIMPLEMENTED",
    "B05_UID_GID_ALLOCATION_UNAVAILABLE",
    "B06_BUILD_LOADER_CLOSURE_UNAVAILABLE",
    "B07_CROSS_UID_SEAL_UNEXECUTED",
    "B08_BORN_IN_D_AND_STOP_UNINTEGRATED",
    "B09_EXTERNAL_ACTOR_DENIAL_UNPROVEN",
    "B10_ADMIN_CHANGE_AUTHORIZATION_ABSENT",
]
PREFIX = "/usr/local/lib/cyberpilot-native-e-lab/"
ARTIFACT_NAMES = ["fixed-factory", "e-bootstrap", "fixed-worker"]
MANIFEST_FIELDS = {
    "account_tool_effects",
    "ephemeral_paths",
    "one_shot_policy",
    "schema",
    "kind",
    "review_base",
    "apply_state",
    "host_backend",
    "accounts_allocation",
    "qualification",
    "accounts",
    "artifacts",
    "blockers",
    "persistent_paths",
    "persistent_units",
    "daemon_reload",
    "identity_policy",
    "apply_tool",
}
REQUEST_FIELDS = {
    "schema",
    "kind",
    "manager",
    "method",
    "mode",
    "unit_name",
    "factory_state",
    "stdin_fd",
    "stdin_property",
    "aux",
    "restart",
    "limit_properties",
    "delegate_properties",
    "credential_properties",
    "exec_artifact",
    "bus_connection",
    "add_ref",
}
LIMITS = {
    "RuntimeMaxUSec": 30000000,
    "TimeoutStartUSec": 5000000,
    "TimeoutStopUSec": 5000000,
    "MemoryMax": 134217728,
    "MemorySwapMax": 0,
    "TasksMax": 8,
    "CPUQuotaPerSecUSec": 250000,
}
ACCOUNT_TOOL_EFFECTS = {
    "may_modify_databases": ["/etc/passwd", "/etc/group", "/etc/shadow", "/etc/gshadow"],
    "may_replace_existing_backups": [
        "/etc/passwd-",
        "/etc/group-",
        "/etc/shadow-",
        "/etc/gshadow-",
    ],
    "cache_effect": "MAY_FLUSH_NSCD_PASSWD_GROUP_IF_AVAILABLE",
    "other_tool_effects": "UNAVAILABLE_DISTRIBUTION_REVIEW_REQUIRED",
    "authorization": "NOT_GRANTED",
    "rollback": "NO_AUTOMATIC_GLOBAL_DATABASE_OR_BACKUP_RESTORE",
}
CREDENTIALS = {
    "User": "cp-e-lab",
    "Group": "cp-e-lab",
    "CapabilityBoundingSet": 192,
    "AmbientCapabilities": 192,
    "NoNewPrivileges": True,
}
SERVICE = {
    "Type": "exec",
    "User": "cp-e-lab",
    "Group": "cp-e-lab",
    "ExecStart": PREFIX + "e-bootstrap",
    "WorkingDirectory": "/",
    "UMask": "0077",
    "Delegate": "cpu memory pids",
    "DelegateSubgroup": ".supervisor",
    "CapabilityBoundingSet": "CAP_SETUID CAP_SETGID",
    "AmbientCapabilities": "CAP_SETUID CAP_SETGID",
    "NoNewPrivileges": "yes",
    "PrivateUsers": "no",
    "ProtectControlGroups": "no",
    "RestrictNamespaces": "yes",
    "RestrictAddressFamilies": "AF_UNIX",
    "SystemCallArchitectures": "native",
    "LimitCORE": "0",
    "RuntimeMaxSec": "30s",
    "TimeoutStartSec": "5s",
    "TimeoutStopSec": "5s",
    "MemoryMax": "128M",
    "MemorySwapMax": "0",
    "TasksMax": "8",
    "CPUQuota": "25%",
    "KillMode": "control-group",
    "SendSIGKILL": "yes",
    "Restart": "no",
    "StandardOutput": "null",
    "StandardError": "null",
}
ACCOUNTS = [
    'u cp-e-lab - "CyberPilot research E" /nonexistent /usr/sbin/nologin',
    'u cp-w-lab - "CyberPilot research W" /nonexistent /usr/sbin/nologin',
]
# Exact source-context pins inserted once from the preserved review base below.
PINNED: dict[str, str] = {
    "ADMISSION_FENCE_CUSTODY_ADR.md": (
        "5d8fd6c4a8c17ff3d8a51f56376558f990655eb29633c09f4bb72ddc83ce8573"
    ),
    "NATIVE_E_PROVISIONING_PLAN.md": (
        "27cf1e2de8159ef70fd6446a464dedb2e95881504c45f6cad90436e82b48644b"
    ),
    "evidence_worker_entry.json": (
        "c34cdf8aea4cb8686fca83b27e046ff03761a41ab5b9caa5fd6b3a6461bd1fda"
    ),
    "research/credential_seal/seal.c": (
        "ffb54d7f05e5d5b8c47ab557eea53e8b52e014f30829ee6bcb47b25fb01724f8"
    ),
    "research/credential_seal/seal.h": (
        "3eb902431f4f3faf96c36a5b96bef4bd12ae77143ed9957f2ced413bc4d01f07"
    ),
    "research/parent_handoff/handoff.c": (
        "fb23fd48e35ee049f5fd3b8f3fd9164b2156e511dbd2d056577649f142835c16"
    ),
    "research/worker_entry/entry_credential.c": (
        "a2655d57466afae8438d87077cd60b0c5fa8ab8a498a4ff116efa7f38dab621a"
    ),
    "research/worker_entry/entry_credential.h": (
        "4599ce0d2832e4801fc82befd444357c998d2b51bcd31c6bc728d836c2121089"
    ),
    "research/worker_entry/fixed_worker.c": (
        "2462b5cfc2f7d76b473f29fec184154941d1a19ec30b06f75c29ee02c69dfe03"
    ),
    "research/worker_entry/integration.c": (
        "3a39ddd4539e2bd3cbe78b1a9e237414c9d5a959fdd9f5462b6037e01b448241"
    ),
    "src/native_e_lab/domain.py": (
        "2b15835c7a9414d9f402ef9452e911fabbfbcb45841650846a9302243cea1da6"
    ),
    "src/native_e_lab/domain_gate.py": (
        "8731581a32092e39aac4b6753c2ca4d125af6c8b437a90fd4fd67dc5e411993e"
    ),
    "src/native_e_lab/domain_supervisor.c": (
        "e19ebd8c77df6bb47fdb1dd5e3561ee4caacb0e8515a946e78c14bdbc078898b"
    ),
    "src/native_e_lab/domain_worker.c": (
        "39d904f0349c244e69f6823478ce4236c26b826faaa9ff2e266d8ee4f6389959"
    ),
    "src/native_e_lab/gate.py": (
        "64985d27d97338ec37240cae7e3fca5c1beaa2a50d2f87290b992f31cafe47af"
    ),
    "src/native_e_lab/handles.py": (
        "ff9e85ab822ac3233cb3ca845e32ffd7b33610397bb97a042c83258502b5c867"
    ),
    "src/native_e_lab/lab.py": ("ecd1be165ca4f81ae6275ad780010593bef797b3d387609851956d0ad5554db0"),
    "src/native_e_lab/protocol.py": (
        "6b7449d8144f958c14202b63cb61b79c350c35f0e5b3e2f68c212d4056db3a44"
    ),
}


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON key")
        result[name] = value
    return result


def _no_number(token: str) -> Any:
    raise ValueError("non-integer JSON number forbidden")


def _json(text: str) -> dict[str, Any]:
    if len(text) > 65536 or "\0" in text:
        raise ValueError("invalid bounded JSON")
    value = json.loads(
        text, object_pairs_hook=_object, parse_constant=_no_number, parse_float=_no_number
    )
    if not isinstance(value, dict):
        raise ValueError("object required")
    return value


def _supported_config(text: str) -> bool:
    return all(c in "\t\r\n" or 32 <= ord(c) < 127 for c in text)


def _inspect(
    manifest: dict[str, Any],
    request: dict[str, Any],
    pins: dict[str, Any],
    unit: str,
    users: str,
    actual: dict[str, str],
) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, label: str) -> None:
        if not condition:
            errors.append(label)

    require(set(manifest) == MANIFEST_FIELDS, "manifest fields")
    require(type(manifest.get("schema")) is int and manifest["schema"] == 1, "manifest schema")
    expected: dict[str, Any] = {
        "kind": "ADMIN_REVIEW_ONLY",
        "review_base": BASE,
        "apply_state": "BLOCKED",
        "host_backend": "MISSING",
        "accounts_allocation": "UNAVAILABLE",
        "qualification": "UNCHANGED_UNBOUND",
        "accounts": ["cp-e-lab", "cp-w-lab"],
        "persistent_units": "NONE",
        "daemon_reload": "NOT_REQUIRED_BY_PROPOSED_TRANSIENT_STRATEGY",
        "identity_policy": "RESERVE_ON_UNKNOWN_NO_UID_REUSE",
        "apply_tool": "NOT_IMPLEMENTED",
        "persistent_paths": [
            "/etc/sysusers.d/cyberpilot-native-e-lab.conf",
            PREFIX.rstrip("/"),
            "/etc/cyberpilot-native-e-lab",
            "/etc/cyberpilot-native-e-lab/manifest.json",
            "/var/lib/cyberpilot-native-e-lab",
            "/var/lib/cyberpilot-native-e-lab/attempt.intent",
        ],
        "ephemeral_paths": [
            "/run/systemd/transient/cyberpilot-native-e-lab-<factory_nonce>.service",
            "MANAGER_OWNED_NEW_CGROUP_P_UNAVAILABLE",
        ],
        "one_shot_policy": "ROOT_EXCLUSIVE_FSYNC_DENY_ONLY_MARKER_NEVER_REATTACH",
        "account_tool_effects": ACCOUNT_TOOL_EFFECTS,
        "blockers": BLOCKERS,
        "artifacts": [
            {
                "name": name,
                "path": PREFIX + name,
                "owner": "root:root",
                "mode": "0555",
                "sha256": "UNAVAILABLE",
            }
            for name in ARTIFACT_NAMES
        ],
    }
    for key, value in expected.items():
        require(manifest.get(key) == value, "manifest " + key)
    require(set(request) == REQUEST_FIELDS, "request fields")
    require(type(request.get("schema")) is int and request["schema"] == 1, "request schema")
    request_expected: dict[str, Any] = {
        "kind": "REQUEST_CONTRACT_ONLY",
        "manager": "SYSTEM_MANAGER",
        "method": "StartTransientUnit",
        "mode": "fail",
        "unit_name": "cyberpilot-native-e-lab-<factory_nonce>.service",
        "factory_state": "UNIMPLEMENTED",
        "stdin_fd": "LIVE_FACTORY_E_ENDPOINT_UNAVAILABLE",
        "stdin_property": {"name": "StandardInputFileDescriptor", "signature": "h"},
        "aux": [],
        "restart": "no",
        "limit_properties": LIMITS,
        "delegate_properties": {
            "DelegateControllers": ["cpu", "memory", "pids"],
            "DelegateSubgroup": ".supervisor",
        },
        "credential_properties": CREDENTIALS,
        "exec_artifact": "UNAVAILABLE_NO_CURRENT_RESEARCH_BINARY_ALLOWED",
        "bus_connection": "LOCAL_SYSTEM_BUS_CLIENT",
        "add_ref": True,
    }
    for key, value in request_expected.items():
        # JSON equality alone considers bool equal to int; canonical encodings do not.
        require(
            json.dumps(request.get(key), sort_keys=True) == json.dumps(value, sort_keys=True),
            "request " + key,
        )
    require(set(pins) == {"schema", "revision", "sha256"}, "pin fields")
    require(type(pins.get("schema")) is int and pins["schema"] == 1, "pin schema")
    require(pins.get("revision") == BASE and pins.get("sha256") == PINNED, "pinned source context")
    require(actual == PINNED, "source changed or unavailable")
    try:
        if len(unit) > 16384 or not _supported_config(unit):
            raise ValueError("invalid unit text")
        parser = configparser.ConfigParser(interpolation=None, strict=True)
        parser.optionxform = str  # type: ignore[assignment]
        parser.read_string(unit)
        require(
            not parser.defaults() and set(parser.sections()) == {"Unit", "Service"},
            "unit sections/defaults",
        )
        require(
            dict(parser["Unit"]) == {"Description": "CyberPilot fixed native E research cohort"},
            "unit metadata",
        )
        require(dict(parser["Service"]) == SERVICE, "service properties")
    except (configparser.Error, KeyError, ValueError):
        errors.append("invalid unit")
    if len(users) > 4096 or not _supported_config(users):
        errors.append("account proposal")
        return errors
    lines = [
        line.strip()
        for line in users.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    require(len(users) <= 4096 and "\0" not in users and lines == ACCOUNTS, "account proposal")
    return errors


def check_bundle() -> dict[str, Any]:
    """Read fixed research files, return passive diagnostics only; performs no OS operations."""
    try:
        documents = [
            _json((HERE / name).read_text())
            for name in ["change-manifest.json", "request-contract.json", "source-pins.json"]
        ]
        actual: dict[str, str] = {}
        for name in PINNED:
            path = ROOT / name
            if path.is_symlink() or path.stat().st_size > 524288:
                raise ValueError("source context unavailable")
            actual[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        errors = _inspect(
            documents[0],
            documents[1],
            documents[2],
            (HERE / "cohort.service.proposed").read_text(),
            (HERE / "accounts.conf.proposed").read_text(),
            actual,
        )
    except (OSError, ValueError, TypeError):
        errors = ["bundle unavailable or malformed"]
    if errors:
        return {
            "content_check": "FAIL",
            "apply": "BLOCKED",
            "host_commands": "NOT_IMPLEMENTED",
            "errors": errors,
        }
    return {"content_check": "PASS", "apply": "BLOCKED", "host_commands": "NOT_IMPLEMENTED"}


if __name__ == "__main__":
    result = check_bundle()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["content_check"] == "PASS" else 1)
