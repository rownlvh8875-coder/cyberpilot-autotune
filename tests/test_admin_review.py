"""Offline review lint, not runtime admission or a host executor."""

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "research/admin_review"
SPEC = importlib.util.spec_from_file_location("admin_bundle_check", BUNDLE / "check_bundle.py")
assert SPEC is not None and SPEC.loader is not None
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


@pytest.fixture
def data():
    manifest = CHECK._json((BUNDLE / "change-manifest.json").read_text())
    request = CHECK._json((BUNDLE / "request-contract.json").read_text())
    pins = CHECK._json((BUNDLE / "source-pins.json").read_text())
    unit = (BUNDLE / "cohort.service.proposed").read_text()
    users = (BUNDLE / "accounts.conf.proposed").read_text()
    return manifest, request, pins, unit, users, copy.deepcopy(pins["sha256"])


def check(data):
    return CHECK._inspect(*data)


def test_consistent_bundle_still_blocks_apply_and_has_no_host_effects(data):
    before = copy.deepcopy(data)
    result = check(data)
    assert data == before
    assert result == []
    result = subprocess.run(
        [sys.executable, str(BUNDLE / "check_bundle.py")],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "content_check": "PASS",
        "apply": "BLOCKED",
        "host_commands": "NOT_IMPLEMENTED",
    }


@pytest.mark.parametrize(
    "old,new",
    [
        ("User=cp-e-lab", "User=root"),
        ("Group=cp-e-lab", "Group=root"),
        ("Type=exec", "Type=simple"),
        ("Restart=no", "Restart=always"),
        ("NoNewPrivileges=yes", "NoNewPrivileges=no"),
        ("CAP_SETUID CAP_SETGID", "CAP_SETUID CAP_SETGID CAP_KILL"),
        ("MemoryMax=128M", "MemoryMax=infinity"),
        ("MemorySwapMax=0", "MemorySwapMax=128M"),
        ("TasksMax=8", "TasksMax=64"),
        ("CPUQuota=25%", "CPUQuota=100%"),
        ("RuntimeMaxSec=30s", "RuntimeMaxSec=infinity"),
        ("TimeoutStopSec=5s", "TimeoutStopSec=30s"),
        ("DelegateSubgroup=.supervisor", "DelegateSubgroup="),
        ("Delegate=cpu memory pids", "Delegate=yes"),
        (
            "ExecStart=/usr/local/lib/cyberpilot-native-e-lab/e-bootstrap",
            "ExecStart=/bin/sh -c payload",
        ),
    ],
)
def test_unsafe_unit_change_rejected(data, old, new):
    changed = list(data)
    changed[3] = changed[3].replace(old, new)
    assert check(changed)


@pytest.mark.parametrize(
    "addition",
    [
        "ExecStartPost=/bin/true",
        "ExecStop=/bin/kill -9 1",
        "Environment=LD_PRELOAD=evil",
        "EnvironmentFile=/tmp/creds",
        "StandardInput=null",
        "StandardInputFileDescriptor=0",
        "Sockets=public.socket",
        "OpenFile=/tmp/untrusted",
        "BindPaths=/home",
        "SupplementaryGroups=sudo",
        "User=cp-e-lab",
        "[Install]\nWantedBy=multi-user.target",
        "[DEFAULT]\nInjected=yes",
    ],
)
def test_extra_unit_directive_duplicate_or_section_rejected(data, addition):
    changed = list(data)
    changed[3] += "\n" + addition + "\n"
    assert check(changed)


@pytest.mark.parametrize(
    "field,value",
    [
        ("apply_state", "READY"),
        ("kind", "APPROVAL_RECORD"),
        ("review_base", "0" * 40),
        ("accounts_allocation", 17001),
        ("host_backend", "IMPLEMENTED"),
        ("schema", True),
    ],
)
def test_review_record_cannot_be_relabelled_as_apply_authority(data, field, value):
    data[0][field] = value
    assert check(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("mode", "replace"),
        ("factory_state", "READY"),
        ("stdin_fd", 0),
        ("unit_name", "existing.service"),
        ("manager", "USER_MANAGER"),
        ("bus_connection", "DIRECT_MANAGER_SOCKET"),
        ("add_ref", False),
        ("method", "StartUnit"),
    ],
)
def test_request_contract_rejects_attach_replace_and_serialized_fd(data, field, value):
    data[1][field] = value
    assert check(data)


def test_missing_or_modified_source_pin_rejected(data):
    data[5][next(iter(data[5]))] = "0" * 64
    assert check(data)


def test_pin_set_cannot_be_shrunk(data):
    name = next(iter(data[2]["sha256"]))
    del data[2]["sha256"][name]
    del data[5][name]
    assert check(data)


def test_placeholder_artifact_cannot_become_fabricated_build_evidence(data):
    data[0]["artifacts"][0]["sha256"] = "1" * 64
    assert check(data)


def test_qualification_cannot_be_promoted(data):
    data[0]["qualification"] = "BOUND"
    assert check(data)


def test_account_mapping_or_login_shell_change_rejected(data):
    changed = list(data)
    changed[4] = changed[4].replace("/usr/sbin/nologin", "/bin/bash")
    assert check(changed)


def test_missing_blocker_is_rejected(data):
    data[0]["blockers"].pop()
    assert check(data)


@pytest.mark.parametrize(
    "text",
    [
        '{"schema":1,"schema":1}',
        "[]",
        '{"x":NaN}',
        '{"x":Infinity}',
        '{"x":-Infinity}',
        '{"x":1e999}',
        "\0",
        " " * 65537,
    ],
)
def test_duplicate_json_non_object_or_nonfinite_values_rejected(text):
    with pytest.raises(ValueError):
        CHECK._json(text)


def test_no_generic_apply_or_resource_operations_exposed():
    text = (BUNDLE / "check_bundle.py").read_text()
    assert all(
        token not in text
        for token in [
            "import subprocess",
            "import socket",
            "import ctypes",
            "os.system",
            "Popen(",
        ]
    )


def test_missing_bundle_files_return_blocked(monkeypatch, tmp_path):
    monkeypatch.setattr(CHECK, "HERE", tmp_path)
    result = CHECK.check_bundle()
    assert result["content_check"] == "FAIL" and result["apply"] == "BLOCKED"


def test_symlink_source_is_not_read_as_source_context(monkeypatch, tmp_path):
    name = next(iter(CHECK.PINNED))
    file = tmp_path / name
    file.parent.mkdir(parents=True, exist_ok=True)
    file.symlink_to(ROOT / name)
    monkeypatch.setattr(CHECK, "ROOT", tmp_path)
    result = CHECK.check_bundle()
    assert result["content_check"] == "FAIL" and result["apply"] == "BLOCKED"


def test_file_source_drift_is_detected_before_consistency_pass(monkeypatch, tmp_path):
    import shutil

    for name in CHECK.PINNED:
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, file)
    changed = tmp_path / next(iter(CHECK.PINNED))
    with changed.open("a") as stream:
        stream.write("\n")
    monkeypatch.setattr(CHECK, "ROOT", tmp_path)
    result = CHECK.check_bundle()
    assert result["content_check"] == "FAIL"
    assert "source changed or unavailable" in result["errors"]


@pytest.mark.parametrize("invalid", ["\0", "x" * 16385, "[Service]\nType=exec\n"])
def test_invalid_or_missing_unit_text_is_rejected(data, invalid):
    changed = list(data)
    changed[3] = invalid
    assert check(changed)


@pytest.mark.parametrize("space", ["\u00a0", "\u2009", "\v", "\f", "\x7f"])
def test_unsupported_key_whitespace_never_hides_security_directive(data, space):
    changed = list(data)
    changed[3] = changed[3].replace("NoNewPrivileges=yes", "NoNewPrivileges" + space + "=yes")
    assert check(changed)


def test_unsupported_account_prefix_not_normalized(data):
    changed = list(data)
    changed[4] = changed[4].replace("u cp-e-lab", "\u00a0u cp-e-lab")
    assert check(changed)


def test_global_account_effects_are_explicit_even_while_apply_blocked(data):
    effects = data[0].get("account_tool_effects")
    assert effects == {
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


@pytest.mark.parametrize("field", ["may_replace_existing_backups", "cache_effect"])
def test_account_effect_cannot_be_omitted(data, field):
    effects = copy.deepcopy(data[0].get("account_tool_effects", {}))
    effects.pop(field, None)
    data[0]["account_tool_effects"] = effects
    assert check(data)
