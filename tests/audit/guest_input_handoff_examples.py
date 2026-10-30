"""Literal synthetic acceptance examples, independent of the reference oracle."""

import copy
import hashlib
import json
from typing import Any

CASES = (
    ("fd_zero", "SYNTHETIC_GRAPH_CONSISTENT", None),
    ("same_content_distinct_objects", "SYNTHETIC_GRAPH_CONSISTENT", None),
    ("empty_file", "SYNTHETIC_GRAPH_CONSISTENT", None),
    ("manifest_order", "SYNTHETIC_GRAPH_CONSISTENT", None),
    ("declared_not_read", "SYNTHETIC_GRAPH_CONSISTENT", None),
    ("future_write_only", "REJECTED", "SEAL_INVALID"),
    ("chmod_only", "REJECTED", "SEAL_INVALID"),
    ("seal_unavailable", "REJECTED", "SEAL_INVALID"),
    ("wrong_inode_same_bytes", "REJECTED", "OBJECT_BINDING_MISMATCH"),
    ("wrong_object_generation", "REJECTED", "OBJECT_BINDING_MISMATCH"),
    ("wrong_pin_generation", "REJECTED", "OBJECT_BINDING_MISMATCH"),
    ("namespace_changed", "REJECTED", "CONTEXT_MISMATCH"),
    ("source_changed", "REJECTED", "CONTEXT_MISMATCH"),
    ("different_consumer_table", "REJECTED", "CONTEXT_MISMATCH"),
    ("read_before_ready", "REJECTED", "PHASE_ORDER"),
    ("extra_fd", "REJECTED", "INVENTORY_INCOMPLETE"),
    ("inventory_unknown", "REJECTED", "INVENTORY_INCOMPLETE"),
    ("inventory_zero_unknown", "REJECTED", "INVENTORY_INCOMPLETE"),
    ("inventory_hash_wrong", "REJECTED", "INVENTORY_DIGEST_MISMATCH"),
    ("transfer_subset", "REJECTED", "MANIFEST_SET_MISMATCH"),
    ("transfer_duplicate", "REJECTED", "MANIFEST_SET_MISMATCH"),
    ("duplicate_name", "REJECTED", "MANIFEST_INVALID"),
    ("same_object_alias", "REJECTED", "MANIFEST_INVALID"),
    ("missing_pin", "REJECTED", "PIN_LIFETIME_INVALID"),
    ("early_release", "REJECTED", "PIN_LIFETIME_INVALID"),
    ("seal_before_pin", "REJECTED", "PIN_LIFETIME_INVALID"),
    ("read_after_close", "REJECTED", "FD_LIFETIME_INVALID"),
    ("stale_binding_generation", "REJECTED", "FD_LIFETIME_INVALID"),
    ("stale_ofd", "REJECTED", "FD_LIFETIME_INVALID"),
    ("writable_descriptor", "REJECTED", "FD_ACCESS_INVALID"),
    ("cloexec_missing", "REJECTED", "FD_ACCESS_INVALID"),
    ("exec_after_ready", "REJECTED", "UNSUPPORTED_OPERATION"),
    ("dup_after_ready", "REJECTED", "UNSUPPORTED_OPERATION"),
    ("shared_files_clone", "REJECTED", "UNSUPPORTED_OPERATION"),
    ("pathname_reopen", "REJECTED", "UNSUPPORTED_OPERATION"),
    ("mmap_as_read", "REJECTED", "UNSUPPORTED_OPERATION"),
    ("partial_as_full", "REJECTED", "FULL_FILE_STAGE_REQUIRED"),
    ("wrong_returned_bytes", "REJECTED", "READ_CONTENT_MISMATCH"),
    ("unknown_returned_bytes", "REJECTED", "SCHEMA_INVALID"),
    ("duplicate_sequence", "REJECTED", "TIME_ORDER_INVALID"),
    ("backward_time", "REJECTED", "TIME_ORDER_INVALID"),
    ("wrong_clock", "REJECTED", "CLOCK_DOMAIN_INVALID"),
    ("missing_end", "REJECTED", "INCOMPLETE_GRAPH"),
    ("bool_fd", "REJECTED", "SCHEMA_INVALID"),
    ("dropped_event", "REJECTED", "COMPLETION_INVALID"),
    ("failed_exit", "REJECTED", "COMPLETION_INVALID"),
    ("missing_binding", "REJECTED", "MANIFEST_SET_MISMATCH"),
    ("stale_transfer", "REJECTED", "TRANSFER_COHORT_MISMATCH"),
    ("rebind_after_ready", "REJECTED", "PHASE_ORDER"),
    ("wrong_sealed_size", "REJECTED", "SEAL_INVALID"),
    ("observed_not_synthetic", "REJECTED", "EVIDENCE_KIND_UNSUPPORTED"),
    ("unknown_drop_count", "REJECTED", "COMPLETION_INVALID"),
    ("extra_event_field", "REJECTED", "SCHEMA_INVALID"),
    ("same_ofd_different_objects", "REJECTED", "FD_ALIAS_UNSUPPORTED"),
    ("manifest_digest_wrong", "REJECTED", "MANIFEST_DIGEST_MISMATCH"),
    ("bundle_digest_wrong", "REJECTED", "TRANSFER_COHORT_MISMATCH"),
    ("release_missing", "REJECTED", "PIN_LIFETIME_INVALID"),
)


def _hash(value: Any) -> str:
    # Fixture construction uses stdlib directly, never oracle canonical helpers.
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def complete(count: int = 1, *, empty: bool = False, read: bool = True) -> dict[str, Any]:
    raw = b"" if empty else b"0123456789ABCDEF\n"
    members = [
        {
            "name": f"data/item{i}",
            "object_id": f"object{i}",
            "object_generation": 0,
            "pin_generation": 0,
            "dev": 1,
            "ino": 10 + i,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        for i in range(count)
    ]
    context = {
        "session_id": "synthetic-session",
        "attempt_id": "synthetic-attempt",
        "namespace_generation": 0,
        "source_revision": "a" * 40,
        "vm_profile_digest": "b" * 64,
        "observer_profile_digest": "c" * 64,
        "consumer_image_digest": "d" * 64,
        "consumer_task_generation": 1,
        "consumer_exec_generation": 1,
        "consumer_fd_table_generation": 1,
        "clock_domain": "GUEST_HANDOFF_OBSERVATION_MONOTONIC_NS",
        "manifest_digest": _hash({"schema": "guest-data-input-set-v1", "members": members}),
    }
    ctx = _hash(context)
    refs = [{"object_id": m["object_id"], "object_generation": 0} for m in members]
    bundle = _hash(
        {
            "schema": "guest-data-fd-bundle-v1",
            "context_digest": ctx,
            "transfer_generation": 0,
            "members": refs,
        }
    )
    bindings = [
        {
            "transfer_generation": 0,
            **{
                k: m[k]
                for k in (
                    "object_id",
                    "object_generation",
                    "pin_generation",
                    "dev",
                    "ino",
                    "bytes",
                    "sha256",
                )
            },
            "fd": 0 if i == 0 else i + 2,
            "binding_generation": 0,
            "ofd_id": f"ofd{i}",
            "ofd_generation": 0,
            "access_mode": "RDONLY",
            "cloexec": True,
            "seal_mask": 47,
        }
        for i, m in enumerate(members)
    ]

    def inventory(rows: list[dict[str, Any]]) -> str:
        return _hash(
            {"schema": "guest-data-fd-inventory-v1", "context_digest": ctx, "bindings": rows}
        )

    rows: list[tuple[str, dict[str, Any]]] = []

    def add(kind: str, data: dict[str, Any]) -> None:
        rows.append((kind, data))

    for m in members:
        pin = {k: m[k] for k in ("object_id", "object_generation", "pin_generation", "dev", "ino")}
        add("PIN", pin)
        add("SEAL", {**pin, "seal_mask": 47, "bytes": m["bytes"], "sha256": m["sha256"]})
    add("STOPPED", {"inventory_digest": inventory([]), "complete": True, "extra_fd_count": 0})
    add("TRANSFER", {"transfer_generation": 0, "bundle_digest": bundle, "members": refs})
    for b in bindings:
        add("BIND", b)
    add(
        "READY",
        {
            "transfer_generation": 0,
            "bundle_digest": bundle,
            "inventory_digest": inventory(bindings),
            "complete": True,
            "extra_fd_count": 0,
        },
    )
    for b in bindings:
        ref = {k: b[k] for k in ("fd", "binding_generation", "ofd_id", "ofd_generation")}
        if read:
            add(
                "PREAD_FULL",
                {
                    "transfer_generation": 0,
                    **ref,
                    "offset": 0,
                    "returned_len": len(raw),
                    "returned_bytes_hex": raw.hex(),
                },
            )
        add("CLOSE", ref)
    add("FINISH", {"exit_kind": "EXITED", "exit_code": 0, "complete": True, "drop_count": 0})
    for m in members:
        add("RELEASE", {k: m[k] for k in ("object_id", "object_generation", "pin_generation")})
    add("END", {})
    return {
        "schema": "guest-input-handoff-design-v1",
        "evidence_kind": "SYNTHETIC",
        "context": context,
        "manifest": members,
        "events": [
            {"seq": i, "time_ns": i + 10, "context_digest": ctx, "kind": kind, "data": data}
            for i, (kind, data) in enumerate(rows)
        ],
    }


def event(graph: dict[str, Any], kind: str, ordinal: int = 0) -> dict[str, Any]:
    events: list[dict[str, Any]] = graph["events"]
    return [e for e in events if e["kind"] == kind][ordinal]


def example(case: str) -> dict[str, Any]:
    if case not in {c[0] for c in CASES}:
        raise ValueError("unknown synthetic example")
    g = complete(
        2
        if case in ("same_content_distinct_objects", "manifest_order", "same_ofd_different_objects")
        else 1,
        empty=case == "empty_file",
        read=case != "declared_not_read",
    )
    edits = {
        "future_write_only": ("SEAL", {"seal_mask": 55}),
        "chmod_only": ("SEAL", {"seal_mask": 1}),
        "seal_unavailable": ("SEAL", {"seal_mask": None}),
        "wrong_inode_same_bytes": ("BIND", {"ino": 999}),
        "wrong_object_generation": ("BIND", {"object_generation": 1}),
        "wrong_pin_generation": ("BIND", {"pin_generation": 1}),
        "extra_fd": ("READY", {"extra_fd_count": 1}),
        "inventory_unknown": ("READY", {"complete": None}),
        "inventory_zero_unknown": ("STOPPED", {"extra_fd_count": None}),
        "inventory_hash_wrong": ("READY", {"inventory_digest": "e" * 64}),
        "stale_binding_generation": ("PREAD_FULL", {"binding_generation": 1}),
        "stale_ofd": ("PREAD_FULL", {"ofd_id": "other-ofd"}),
        "writable_descriptor": ("BIND", {"access_mode": "RDWR"}),
        "cloexec_missing": ("BIND", {"cloexec": False}),
        "partial_as_full": ("PREAD_FULL", {"returned_len": 4, "returned_bytes_hex": "30313233"}),
        "wrong_returned_bytes": ("PREAD_FULL", {"returned_bytes_hex": b"X123456789ABCDEF\n".hex()}),
        "unknown_returned_bytes": ("PREAD_FULL", {"returned_bytes_hex": None}),
        "bool_fd": ("BIND", {"fd": True}),
        "dropped_event": ("FINISH", {"drop_count": 1}),
        "failed_exit": ("FINISH", {"exit_code": 2}),
        "stale_transfer": ("PREAD_FULL", {"transfer_generation": 1}),
        "wrong_sealed_size": ("SEAL", {"bytes": 18}),
        "unknown_drop_count": ("FINISH", {"drop_count": None}),
        "bundle_digest_wrong": ("TRANSFER", {"bundle_digest": "e" * 64}),
    }
    if case in edits:
        kind, patch = edits[case]
        event(g, kind)["data"].update(patch)
    elif case == "manifest_order":
        g["manifest"].reverse()
    elif case in ("namespace_changed", "source_changed"):
        g["context"][
            "namespace_generation" if case == "namespace_changed" else "source_revision"
        ] = 1 if case == "namespace_changed" else "e" * 40
    elif case == "different_consumer_table":
        event(g, "PREAD_FULL")["context_digest"] = "e" * 64
    elif case in ("read_before_ready", "early_release", "seal_before_pin", "read_after_close"):
        first, second = {
            "read_before_ready": ("PREAD_FULL", "READY"),
            "early_release": ("RELEASE", "PREAD_FULL"),
            "seal_before_pin": ("SEAL", "PIN"),
            "read_after_close": ("CLOSE", "PREAD_FULL"),
        }[case]
        node = event(g, first)
        g["events"].remove(node)
        g["events"].insert(g["events"].index(event(g, second)), node)
        for i, e in enumerate(g["events"]):
            e.update(seq=i, time_ns=i + 10)
    elif case in ("transfer_subset", "transfer_duplicate"):
        refs = event(g, "TRANSFER")["data"]["members"]
        refs.clear() if case == "transfer_subset" else refs.append(copy.deepcopy(refs[0]))
    elif case in ("duplicate_name", "same_object_alias"):
        duplicate = copy.deepcopy(g["manifest"][0])
        if case == "same_object_alias":
            duplicate["name"] = "data/alias"
        g["manifest"].append(duplicate)
    elif case in ("missing_pin", "missing_binding", "missing_end", "release_missing"):
        kind = {
            "missing_pin": "PIN",
            "missing_binding": "BIND",
            "missing_end": "END",
            "release_missing": "RELEASE",
        }[case]
        g["events"].remove(event(g, kind))
        for i, e in enumerate(g["events"]):
            e.update(seq=i, time_ns=i + 10)
    elif case in (
        "exec_after_ready",
        "dup_after_ready",
        "shared_files_clone",
        "pathname_reopen",
        "mmap_as_read",
    ):
        event(g, "PREAD_FULL")["kind"] = {
            "exec_after_ready": "EXEC",
            "dup_after_ready": "DUP",
            "shared_files_clone": "CLONE_FILES",
            "pathname_reopen": "OPEN_PATH",
            "mmap_as_read": "MMAP",
        }[case]
    elif case == "duplicate_sequence":
        event(g, "PREAD_FULL")["seq"] = 0
    elif case == "backward_time":
        event(g, "PREAD_FULL")["time_ns"] = 1
    elif case == "wrong_clock":
        g["context"]["clock_domain"] = "WALL_CLOCK"
    elif case == "rebind_after_ready":
        g["events"].insert(
            g["events"].index(event(g, "PREAD_FULL")), copy.deepcopy(event(g, "BIND"))
        )
        for i, e in enumerate(g["events"]):
            e.update(seq=i, time_ns=i + 10)
    elif case == "observed_not_synthetic":
        g["evidence_kind"] = "OBSERVED_UNTRUSTED"
    elif case == "extra_event_field":
        event(g, "BIND")["data"]["caller_approved"] = True
    elif case == "same_ofd_different_objects":
        event(g, "BIND", 1)["data"]["ofd_id"] = "ofd0"
    elif case == "manifest_digest_wrong":
        g["context"]["manifest_digest"] = "e" * 64
    return g
