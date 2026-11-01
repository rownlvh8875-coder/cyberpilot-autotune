"""Fixed cached content only. No download, compiler, QEMU or executable invocation."""

import json
from pathlib import Path
from typing import Any, NoReturn

from compatibility.guest_input_closure.elf import inspect_elf
from compatibility.guest_input_closure.filesystem import read_regular
from tests.deny_fd_v2 import build as producer_build
from tests.deny_fd_v2.contracts import PERMISSIONS

from .contracts import AssetBundle, canonical, digest, need

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "docs/evidence/deny_fd_v2_harness_assets_v1.json"
VM = Path("/workspace/scratch/qemu-vm.Hkx9tc/sysroot")
PROBE_ROOT = Path("/workspace/verification-archive/deny-fd-v2-source.LbkXkT/compile-M2481b84")
PROFILE: dict[str, Any] = {
    "schema": "deny-fd-v2-harness-assets-v1",
    "source_revision": "2481b84405beda95a394d1ca0248d7c9d632d28b",
    "source_manifest_digest": "1255f050f56240afe14d4fa7479692ed07b00bf59a6396fa6919354d07ace166",
    "vm_cohort_digest": "d98a259c5a45b56811d40a94e23e50a51ee88b513bb632396f45da6017f7af0c",
    "kernel_sha256": "8d8530d93852968b43c50a11a6c571628e16c074194bc3d293f64871e64e5475",
    "probe": {
        "sha256": "0eb1891fe5c25a04e5447c637f81fb86a80404efbf8602b1ea31bf4d6a342f41",
        "bytes": 915376,
    },
    "busybox": {
        "sha256": "7ae95c260622412ceba6eb9f45d68f616cdc091a1d71d6c0a08b5875bb2c31dd",
        "bytes": 2024544,
    },
    "build_record_sha256": "730e9cc3815af4332be13aba19019a6ee59f8cfc08b0d9e14a54fb8be5970a2b",
    "runtime_qualified": False,
    "build_input_closure_qualified": False,
    "permissions": dict(PERMISSIONS),
}


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        need(key not in result, "duplicate metadata key")
        result[key] = value
    return result


def _invalid(value: str) -> NoReturn:
    raise ValueError("nonfinite metadata forbidden")


def _json(raw: bytes) -> dict[str, Any]:
    data = json.loads(raw, object_pairs_hook=_unique, parse_constant=_invalid)
    need(type(data) is dict, "metadata object required")
    assert isinstance(data, dict)
    return data


def _producer_identity() -> tuple[str, str]:
    data, revision, _ = producer_build._verified_sources()
    return revision, digest(canonical(data))


def _vm_busybox() -> bytes:
    from compatibility.guest_input_closure.contracts import InputSnapshot
    from compatibility.guest_input_closure.filesystem import scan_tree
    from compatibility.guest_input_closure.legacy import _Verifier, _verify_vm

    observed = InputSnapshot(scan_tree("vm_exact_tree", VM))
    _verify_vm(
        _Verifier(
            observed,
            {
                "vm_exact_tree": VM,
                "fixture_selected": Path("/workspace/scratch/guest-backend.FY5icM/build"),
            },
        )
    )
    return read_regular(VM, "usr/bin/busybox", 4 * 1024 * 1024)


def validate_bundle(bundle: AssetBundle) -> None:
    need(type(bundle) is AssetBundle, "fixed asset bundle required")
    bundle.__post_init__()
    need(
        bundle.source_revision == PROFILE["source_revision"]
        and bundle.source_manifest_digest == PROFILE["source_manifest_digest"]
        and bundle.vm_cohort_digest == PROFILE["vm_cohort_digest"]
        and bundle.kernel_sha256 == PROFILE["kernel_sha256"],
        "asset cohort changed",
    )
    for key, raw in (("probe", bundle.probe), ("busybox", bundle.busybox)):
        need(
            len(raw) == PROFILE[key]["bytes"] and digest(raw) == PROFILE[key]["sha256"],
            "fixed asset content changed",
        )
        elf = inspect_elf(raw)
        need(
            elf.machine == 62
            and elf.elf_type == 2
            and elf.interpreter is None
            and not elf.needed
            and not elf.loader_directives
            and elf.rpath is None
            and elf.runpath is None,
            "static fixed x86_64 executable required",
        )


def preflight() -> AssetBundle:
    try:
        profile = _json(read_regular(ROOT, MANIFEST, 1024 * 1024))
        need(canonical(profile) == canonical(PROFILE), "fixed profile changed")
        source, manifest = _producer_identity()
        need(
            (source, manifest) == (PROFILE["source_revision"], PROFILE["source_manifest_digest"]),
            "producer source identity changed",
        )
        raw_record = read_regular(PROBE_ROOT, "build-record.json", 1024 * 1024)
        need(digest(raw_record) == PROFILE["build_record_sha256"], "build record content changed")
        record = _json(raw_record)
        need(
            set(record)
            == {
                "schema",
                "source_revision",
                "source_manifest_digest",
                "compiler_version",
                "command",
                "binary",
                "runtime_qualified",
                "build_input_closure_qualified",
                "permissions",
            },
            "build record shape",
        )
        need(
            record["schema"] == "deny-fd-v2-compile-record-v1"
            and record["source_revision"] == source
            and record["source_manifest_digest"] == manifest
            and record["runtime_qualified"] is False
            and record["build_input_closure_qualified"] is False
            and canonical(record["permissions"]) == canonical(dict(PERMISSIONS)),
            "build record scope/permissions",
        )
        need(
            canonical(record["binary"])
            == canonical({"path": "deny-fd-v2-probe", **PROFILE["probe"]}),
            "build binary identity",
        )
        need(
            type(record["compiler_version"]) is str
            and bool(record["compiler_version"])
            and type(record["command"]) is list
            and bool(record["command"])
            and all(type(v) is str and v for v in record["command"]),
            "compile provenance missing",
        )
        bundle = AssetBundle(
            source,
            manifest,
            PROFILE["vm_cohort_digest"],
            read_regular(PROBE_ROOT, "deny-fd-v2-probe", 4 * 1024 * 1024),
            _vm_busybox(),
            PROFILE["kernel_sha256"],
        )
        validate_bundle(bundle)
        return bundle
    except OSError as error:
        raise ValueError("fixed assets unavailable; no fetch or fallback") from error
