"""Test-only SYNTHETIC serialized lifecycle consistency, never runtime qualification."""

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

Ref = tuple[int, int]
PERMISSIONS = tuple(
    (name, False)
    for name in (
        "build_execution_allowed",
        "promotion_authorized",
        "runtime_qualified",
        "device_class_qualified",
        "policy_adopted",
        "candidate_generation_allowed",
        "application_authorized",
        "runtime_accepted",
        "owner_proposal_allowed",
    )
)
FIELDS = {
    "TABLE_NEW": ("table",),
    "TASK_START": ("task", "table"),
    "OFD_NEW": ("task", "exec", "ofd", "object_digest"),
    "INSTALL": ("task", "table", "epoch", "fd", "slot", "ofd", "cloexec"),
    "DUP": (
        "task",
        "table",
        "epoch",
        "src_fd",
        "src_slot",
        "dst_fd",
        "dst_slot",
        "method",
        "cloexec",
    ),
    "CLOEXEC": ("task", "table", "epoch", "fd", "slot", "old", "new"),
    "CLOSE": ("task", "table", "epoch", "fd", "slot", "ofd"),
    "FORK": ("parent", "table", "epoch", "child", "child_table", "share"),
    "UNSHARE": ("task", "table", "epoch", "after_table"),
    "EXEC": ("task", "table", "epoch", "after_table", "before_exec", "after_exec", "closed"),
    "PIN": ("pin", "ofd"),
    "UNPIN": ("pin", "ofd"),
    "INVENTORY": ("task", "exec", "table", "epoch", "entries"),
    "DETACH": ("task", "exec", "table", "epoch"),
    "REAP": ("task", "exec"),
    "TABLE_FREE": ("table", "epoch", "closed"),
    "OFD_FREE": ("ofd",),
    "END": ("tasks", "tables", "ofds", "pins"),
}


def need(ok: bool, reason: str = "INVALID_STRUCTURE") -> None:
    if not ok:
        raise ValueError(reason)


def uint(value: Any, limit: int = 2**64) -> int:
    need(type(value) is int and 0 <= value < limit, "EXACT_UINT_REQUIRED")
    return int(value)


def boolean(value: Any) -> bool:
    need(type(value) is bool, "EXACT_BOOL_REQUIRED")
    return bool(value)


def ref(value: Any) -> Ref:
    need(type(value) is list and len(value) == 2, "LIFETIME_KEY_REQUIRED")
    return uint(value[0]), uint(value[1])


def shape(value: Any, names: set[str]) -> None:
    need(type(value) is dict and set(value) == names, "CLOSED_FIELD_SET_REQUIRED")


def primitive(value: Any, depth: int = 0, budget: list[int] | None = None) -> None:
    if budget is None:
        budget = [100000, 4 * 1024 * 1024]
    budget[0] -= 1
    need(budget[0] >= 0, "RESOURCE_BOUND")
    need(depth <= 24, "RESOURCE_BOUND")
    if type(value) is dict:
        need(len(value) <= 32 and all(type(k) is str for k in value), "RESOURCE_BOUND")
        for k, v in value.items():
            primitive(k, depth + 1, budget)
            primitive(v, depth + 1, budget)
    elif type(value) is list:
        need(len(value) <= 2048, "RESOURCE_BOUND")
        for v in value:
            primitive(v, depth + 1, budget)
    elif type(value) is str:
        need(len(value) <= 4096, "RESOURCE_BOUND")
        budget[1] -= len(value)
        need(budget[1] >= 0, "RESOURCE_BOUND")
    elif type(value) is int:
        uint(value)
    else:
        need(value is None or type(value) is bool, "INVALID_SCALAR")


def canonical(value: Any) -> bytes:
    primitive(value)
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    need(len(raw) <= 4 * 1024 * 1024, "RESOURCE_BOUND")
    return raw


def context_digest(context: Any) -> str:
    shape(
        context,
        {
            "session_id",
            "boot_scope",
            "source_revision",
            "source_digest",
            "scope_digest",
            "profile",
            "clock_domain",
            "cpus",
        },
    )
    for name in ("session_id", "boot_scope"):
        need(
            type(context[name]) is str
            and re.fullmatch("[a-zA-Z0-9_-]{1,64}", context[name]) is not None,
            "CONTEXT_ID_REQUIRED",
        )
    for name, width in (("source_revision", 40), ("source_digest", 64), ("scope_digest", 64)):
        need(
            type(context[name]) is str
            and re.fullmatch(f"[0-9a-f]{{{width}}}", context[name]) is not None,
            "EXACT_SOURCE_CONTEXT_REQUIRED",
        )
    need(
        context["profile"] == "PROPOSED_KERNEL_SERIALIZED_LIFETIME_V1"
        and context["clock_domain"] == "SYNTHETIC_KERNEL_MONOTONIC_NS",
        "UNSUPPORTED_PROFILE_CLOCK",
    )
    cpus = context["cpus"]
    need(type(cpus) is list and 1 <= len(cpus) <= 8, "CPU_COHORT_REQUIRED")
    checked = [uint(c, 2**32) for c in cpus]
    need(checked == sorted(set(checked)), "CPU_COHORT_REQUIRED")
    return hashlib.sha256(canonical(context)).hexdigest()


@dataclass(frozen=True)
class Decision:
    model_consistent: bool
    reasons: tuple[str, ...]
    digest: str | None
    synthetic_tables: int | None = None
    synthetic_ofds: int | None = None
    status: str = field(default="BLOCKED", init=False)
    actual_dropped_events: None = field(default=None, init=False)
    global_prohibited_counts: None = field(default=None, init=False)
    permissions: tuple[tuple[str, bool], ...] = field(default=PERMISSIONS, init=False)


def entries(value: Any) -> dict[int, tuple[int, Ref, bool]]:
    need(type(value) is list and len(value) <= 64, "INVENTORY_REQUIRED")
    out: dict[int, tuple[int, Ref, bool]] = {}
    order = []
    for row in value:
        need(type(row) is list and len(row) == 4, "INVENTORY_REQUIRED")
        fd = uint(row[0], 64)
        order.append(fd)
        need(fd not in out, "DUPLICATE_FD")
        out[fd] = (uint(row[1]), ref(row[2]), boolean(row[3]))
    need(order == sorted(order), "CANONICAL_INVENTORY_REQUIRED")
    return out


def check(graph: Any) -> tuple[int, int]:
    shape(graph, {"schema", "evidence_class", "context", "events", "coverage"})
    need(
        graph["schema"] == "fd-ofd-lifetime-design-v1"
        and graph["evidence_class"] == "SYNTHETIC_ONLY",
        "SYNTHETIC_ONLY_REQUIRED",
    )
    digest = context_digest(graph["context"])
    events = graph["events"]
    need(type(events) is list and 1 <= len(events) <= 2048, "RESOURCE_BOUND")
    tables: dict[Ref, dict[str, Any]] = {}
    tasks: dict[Ref, dict[str, Any]] = {}
    ofds: dict[Ref, str] = {}
    pins: dict[Ref, Ref] = {}
    registries: dict[str, dict[int, int]] = {k: {} for k in ("tables", "tasks", "ofds", "pins")}
    totals = {k: 0 for k in registries}
    cpu_counts = {cpu: 0 for cpu in graph["context"]["cpus"]}

    def allocate(kind: str, key: Ref, active: Any) -> None:
        last = registries[kind].get(key[0], -1)
        need(
            key[1] == last + 1 and not any(k[0] == key[0] for k in active), "LIFETIME_REUSE_INVALID"
        )
        totals[kind] += 1
        need(totals[kind] <= (32 if kind in ("tasks", "tables") else 64), "RESOURCE_BOUND")
        registries[kind][key[0]] = key[1]

    def table(key: Ref, epoch: Any) -> dict[str, Any]:
        need(key in tables, "TABLE_LIFETIME_UNAVAILABLE")
        need(uint(epoch) == tables[key]["epoch"], "TABLE_EPOCH_MISMATCH")
        return tables[key]

    def task(key: Ref) -> dict[str, Any]:
        need(key in tasks and tasks[key]["table"] is not None, "TASK_LIFETIME_UNAVAILABLE")
        return tasks[key]

    def actor(key: Ref, tk: Ref, epoch: Any) -> dict[str, Any]:
        need(task(key)["table"] == tk, "TASK_TABLE_COHORT_MISMATCH")
        need(
            not any(t["pending"] for t in tasks.values() if t["table"] == tk),
            "INVENTORY_BARRIER_MISSING",
        )
        return table(tk, epoch)

    def clone(old: dict[str, Any], new: Ref) -> None:
        allocate("tables", new, tables)
        slots = {fd: (0, slot[1], slot[2]) for fd, slot in old["slots"].items()}
        tables[new] = {"epoch": 0, "slots": slots, "last": {fd: 0 for fd in slots}}

    for seq, event in enumerate(events, 1):
        shape(event, {"seq", "time_ns", "cpu", "cpu_seq", "context_digest", "kind", "data"})
        need(
            uint(event["seq"]) == seq and event["context_digest"] == digest,
            "SOURCE_ORDER_CONTEXT_MISMATCH",
        )
        uint(event["time_ns"])
        cpu = uint(event["cpu"], 2**32)
        need(cpu in cpu_counts, "CPU_COHORT_REQUIRED")
        cpu_counts[cpu] += 1
        need(uint(event["cpu_seq"]) == cpu_counts[cpu], "SOURCE_SEQUENCE_GAP")
        kind, data = event["kind"], event["data"]
        need(type(kind) is str and kind in FIELDS, "UNSUPPORTED_EFFECT")
        need(type(data) is list and len(data) == len(FIELDS[kind]), "EVENT_ARITY")
        need((kind == "END") == (seq == len(events)), "WINDOW_NOT_CLOSED")
        if kind == "TABLE_NEW":
            need(totals["tables"] == 0 and totals["tasks"] == 0, "ROOT_ALLOCATION_ONLY")
            tk = ref(data[0])
            allocate("tables", tk, tables)
            tables[tk] = {"epoch": 0, "slots": {}, "last": {}}
        elif kind == "TASK_START":
            pk, tk = ref(data[0]), ref(data[1])
            need(
                totals["tasks"] == 0
                and tk in tables
                and tables[tk]["epoch"] == 0
                and not tables[tk]["slots"],
                "ROOT_BIRTH_INVALID",
            )
            allocate("tasks", pk, tasks)
            tasks[pk] = {"table": tk, "exec": 0, "pending": True}
        elif kind == "OFD_NEW":
            pk, ok = ref(data[0]), ref(data[2])
            state = task(pk)
            need(
                not state["pending"] and uint(data[1]) == state["exec"], "TASK_EXEC_COHORT_MISMATCH"
            )
            need(
                type(data[3]) is str and re.fullmatch("[0-9a-f]{64}", data[3]) is not None,
                "OBJECT_CONTEXT_REQUIRED",
            )
            allocate("ofds", ok, ofds)
            ofds[ok] = data[3]
        elif kind in ("INSTALL", "DUP", "CLOEXEC", "CLOSE"):
            pk, tk = ref(data[0]), ref(data[1])
            current = actor(pk, tk, data[2])
            slots = current["slots"]
            fd = uint(data[3], 64)
            sg = uint(data[4])
            if kind == "INSTALL":
                ok = ref(data[5])
                clo = boolean(data[6])
                need(
                    fd not in slots and ok in ofds and sg == current["last"].get(fd, -1) + 1,
                    "BINDING_INSTALL_INVALID",
                )
                slots[fd] = (sg, ok, clo)
                current["last"][fd] = sg
            else:
                need(fd in slots and slots[fd][0] == sg, "SLOT_COHORT_MISMATCH")
                if kind == "DUP":
                    dst = uint(data[5], 64)
                    gen = uint(data[6])
                    clo = boolean(data[8])
                    method = data[7]
                    need(
                        type(method) is str
                        and method in ("DUP", "DUP2", "DUP3", "F_DUPFD", "F_DUPFD_CLOEXEC"),
                        "UNSUPPORTED_EFFECT",
                    )
                    need(
                        fd != dst and gen == current["last"].get(dst, -1) + 1, "DUP_BINDING_INVALID"
                    )
                    need(
                        method == "DUP3" or clo == (method == "F_DUPFD_CLOEXEC"),
                        "DUP_CLOEXEC_MISMATCH",
                    )
                    slots[dst] = (gen, slots[fd][1], clo)
                    current["last"][dst] = gen
                elif kind == "CLOEXEC":
                    before, after = boolean(data[5]), boolean(data[6])
                    need(before == slots[fd][2] and before != after, "CLOEXEC_DELTA_INVALID")
                    slots[fd] = (sg, slots[fd][1], after)
                else:
                    need(ref(data[5]) == slots[fd][1], "OFD_BINDING_MISMATCH")
                    del slots[fd]
            current["epoch"] += 1
        elif kind == "FORK":
            parent, tk, child, ck = ref(data[0]), ref(data[1]), ref(data[3]), ref(data[4])
            current = actor(parent, tk, data[2])
            shared = boolean(data[5])
            if shared:
                need(ck == tk, "SHARED_TABLE_IDENTITY_MISMATCH")
            else:
                need(ck != tk, "FORK_COPY_IDENTITY_MISMATCH")
                clone(current, ck)
            allocate("tasks", child, tasks)
            tasks[child] = {"table": ck, "exec": 0, "pending": True}
        elif kind in ("UNSHARE", "EXEC"):
            pk, tk, new = ref(data[0]), ref(data[1]), ref(data[3])
            current = actor(pk, tk, data[2])
            if new == tk:
                need(
                    sum(t["table"] == tk for t in tasks.values()) == 1,
                    "SHARED_TABLE_UNSHARE_REQUIRED",
                )
            else:
                clone(current, new)
                tasks[pk]["table"] = new
                current = tables[new]
            if kind == "EXEC":
                from_exec, to_exec = uint(data[4]), uint(data[5])
                need(
                    from_exec == tasks[pk]["exec"] and to_exec == from_exec + 1,
                    "EXEC_GENERATION_MISMATCH",
                )
                expected = {fd: s for fd, s in current["slots"].items() if s[2]}
                need(entries(data[6]) == expected, "EXEC_CLOEXEC_DELTA_MISMATCH")
                for fd in expected:
                    del current["slots"][fd]
                if expected:
                    current["epoch"] += 1
                tasks[pk]["exec"] = to_exec
            tasks[pk]["pending"] = True
        elif kind in ("PIN", "UNPIN"):
            key, ok = ref(data[0]), ref(data[1])
            need(ok in ofds, "OFD_LIFETIME_UNAVAILABLE")
            if kind == "PIN":
                allocate("pins", key, pins)
                pins[key] = ok
            else:
                need(key in pins and pins[key] == ok, "PIN_LIFETIME_MISMATCH")
                del pins[key]
        elif kind == "INVENTORY":
            pk, tk = ref(data[0]), ref(data[2])
            state = task(pk)
            current = table(tk, data[3])
            need(
                state["table"] == tk and uint(data[1]) == state["exec"], "TASK_EXEC_COHORT_MISMATCH"
            )
            need(entries(data[4]) == current["slots"], "INVENTORY_MISMATCH")
            state["pending"] = False
        elif kind == "DETACH":
            pk, tk = ref(data[0]), ref(data[2])
            actor(pk, tk, data[3])
            need(uint(data[1]) == tasks[pk]["exec"], "TASK_EXEC_COHORT_MISMATCH")
            tasks[pk]["table"] = None
        elif kind == "REAP":
            pk = ref(data[0])
            need(
                pk in tasks and tasks[pk]["table"] is None and uint(data[1]) == tasks[pk]["exec"],
                "DETACH_REAP_MISMATCH",
            )
            del tasks[pk]
        elif kind == "TABLE_FREE":
            tk = ref(data[0])
            current = table(tk, data[1])
            need(not any(t["table"] == tk for t in tasks.values()), "TABLE_STILL_OWNED")
            need(entries(data[2]) == current["slots"], "TABLE_DESTRUCTION_DELTA_MISMATCH")
            del tables[tk]
        elif kind == "OFD_FREE":
            ok = ref(data[0])
            need(
                ok in ofds
                and ok not in pins.values()
                and not any(s[1] == ok for t in tables.values() for s in t["slots"].values()),
                "OFD_STILL_REFERENCED",
            )
            del ofds[ok]
        else:
            need(
                [uint(v) for v in data] == [totals[k] for k in ("tasks", "tables", "ofds", "pins")],
                "TERMINAL_COUNT_MISMATCH",
            )
            need(not tables and not tasks and not ofds and not pins, "LIFETIMES_NOT_CLOSED")
    coverage = graph["coverage"]
    shape(coverage, {"start_fence", "end_fence", "cpus"})
    need(
        uint(coverage["start_fence"]) == 0 and uint(coverage["end_fence"]) == len(events) + 1,
        "COVERAGE_FENCE_MISMATCH",
    )
    rows = coverage["cpus"]
    need(type(rows) is list and len(rows) == len(cpu_counts), "CPU_COHORT_REQUIRED")
    for row, cpu in zip(rows, cpu_counts, strict=True):
        shape(row, {"cpu", "armed", "drained", "emitted", "last_source_seq", "dropped"})
        need(
            uint(row["cpu"]) == cpu and row["armed"] is True and row["drained"] is True,
            "COVERAGE_NOT_ARMED_DRAINED",
        )
        need(
            uint(row["emitted"]) == cpu_counts[cpu]
            and uint(row["last_source_seq"]) == cpu_counts[cpu]
            and uint(row["dropped"]) == 0,
            "SOURCE_LOSS_OR_UNAVAILABLE",
        )
    return totals["tables"], totals["ofds"]


def evaluate(graph: Any) -> Decision:
    digest = None
    try:
        raw = canonical(graph)
        digest = hashlib.sha256(raw).hexdigest()
        frozen = json.loads(raw)
        tables, ofds = check(frozen)
    except ValueError as exc:
        return Decision(False, (str(exc),), digest)
    return Decision(True, (), digest, tables, ofds)
