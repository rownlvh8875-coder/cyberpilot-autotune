"""Pure observed-frame mapping, not an empirical, executor or application bridge."""

import hashlib
from dataclasses import dataclass, field
from typing import cast

from compatibility.guest_build_receipt.codec import receipt_digest
from compatibility.guest_build_receipt.models import (
    CLOCK_DOMAIN,
    UINT64_MAX,
    BuildCompletion,
    BuildMaterial,
    BuildReceipt,
    EvidenceKind,
    ExitKind,
    InputUse,
    MaterialRole,
    TaskImage,
    UseKind,
)

from .contracts import ConsumptionCapture, ConsumptionProfile, hex_bytes, integer
from .wire import capture_digest

LIMITATIONS = (
    "STOPPED_BUFFER_OBSERVATION_NOT_GENERAL_KERNEL_READ_PROOF",
    "KERNEL_EXEC_LOADER_READS_UNAVAILABLE",
    "MMAP_PAGE_TOUCHES_UNAVAILABLE",
    "OPEN_FILE_DESCRIPTION_ALIAS_CLOSURE_UNQUALIFIED",
    "INPUT_SEAL_BACKEND_UNQUALIFIED",
    "OUTPUT_PROMOTION_BACKEND_UNQUALIFIED",
    "EXTERNAL_EXECUTOR_UNQUALIFIED",
    "RECEIPT_AUTHENTICITY_UNQUALIFIED",
    "GUEST_FULL_INPUT_CLOSURE_UNQUALIFIED",
    "APPLICATION_NOT_AUTHORIZED",
)


@dataclass(frozen=True, slots=True)
class ProducedObservation:
    receipt: BuildReceipt
    trace_window_complete: bool
    profile_reasons: tuple[str, ...]
    capture: ConsumptionCapture
    limitations: tuple[str, ...] = field(default=LIMITATIONS, init=False)
    overall_status: str = field(default="BLOCKED", init=False)
    build_execution_allowed: bool = field(default=False, init=False)
    promotion_authorized: bool = field(default=False, init=False)
    runtime_qualified: bool = field(default=False, init=False)
    device_class_qualified: bool = field(default=False, init=False)
    policy_adopted: bool = field(default=False, init=False)
    candidate_generation_allowed: bool = field(default=False, init=False)
    application_authorized: bool = field(default=False, init=False)
    runtime_accepted: bool = field(default=False, init=False)
    owner_proposal_allowed: bool = field(default=False, init=False)
    successful_prohibited_handles: None = field(default=None, init=False)
    successful_prohibited_effects: None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if (
            type(self.receipt) is not BuildReceipt
            or type(self.trace_window_complete) is not bool
            or type(self.capture) is not ConsumptionCapture
        ):
            raise ValueError("invalid observed diagnostic")
        self.receipt.__post_init__()
        self.capture.__post_init__()
        reasons = tuple(self.profile_reasons)
        if any(type(r) is not str or not r for r in reasons):
            raise ValueError("invalid observed reasons")
        object.__setattr__(self, "profile_reasons", tuple(sorted(set(reasons))))


def produce_receipt(
    capture: ConsumptionCapture, profile: ConsumptionProfile
) -> ProducedObservation:
    capture.__post_init__()
    profile.__post_init__()
    if profile.identity.attempt_id != capture.case or profile.identity.clock_domain != CLOCK_DOMAIN:
        raise ValueError("capture/profile attempt mismatch")
    known = {(m.size, m.sha256): m for m in profile.materials}
    materials: dict[int, BuildMaterial] = {}
    object_keys: set[tuple[int, int]] = set()
    active: dict[int, tuple[int, int, int]] = {}
    parents: dict[int, int | None] = {}
    images: list[TaskImage] = []
    uses: list[InputUse] = []
    reasons: set[str] = set()
    capture_error = False
    root_exit: tuple[ExitKind, int] | None = None
    root_start: int | None = None
    context = receipt_digest(profile.identity)

    def material(ordinal: int) -> BuildMaterial:
        if ordinal not in materials:
            raise ValueError("unknown observed object generation")
        return materials[ordinal]

    def close_image(task: int, finish: int) -> None:
        image, obj, start = active[task]
        m = material(obj)
        images.append(TaskImage(task, image, parents[task], m.material_id, 0, start, finish))

    for event in capture.events[1:-1]:
        if capture_error and event.kind not in ("PAYLOAD", "EXIT"):
            raise ValueError("new observation after fatal capture error")
        v = event.values
        if event.kind == "OBJECT":
            obj = integer(v[0])
            key = (integer(v[1]), integer(v[2]))
            content = (integer(v[3]), cast(str, v[4]))
            if (
                obj != len(materials) + 1
                or key in object_keys
                or content not in known
                or len(materials) >= 64
            ):
                raise ValueError("duplicate/unknown observed object content or generation")
            k = known[content]
            digest = (
                profile.identity.source_digest
                if k.role is MaterialRole.SOURCE
                else profile.identity.toolchain_digest
                if k.role is MaterialRole.TOOLCHAIN
                else profile.identity.environment_digest
            )
            if digest is None:
                raise ValueError("known material cohort unavailable")
            materials[obj] = BuildMaterial(
                k.material_id + "-" + str(obj), 0, k.role, k.logical_path, k.size, k.sha256, digest
            )
            object_keys.add(key)
        elif event.kind == "BIRTH":
            parent = None if v[0] is None else integer(v[0])
            obj = integer(v[1])
            if (
                event.task != len(parents) + 1
                or event.image != 0
                or (parent is None and parents)
                or (parent is not None and (parent not in active or active[parent][1] != obj))
                or len(parents) >= 16
            ):
                raise ValueError("invalid task birth/parent generation")
            if material(obj).role is not MaterialRole.TOOLCHAIN:
                raise ValueError("observed image is not toolchain material")
            parents[event.task] = parent
            if parent is None:
                root_start = event.time_ns
            active[event.task] = (0, obj, event.time_ns)
        elif event.kind == "EXEC":
            if (
                event.task not in active
                or event.image != active[event.task][0] + 1
                or material(integer(v[0])).role is not MaterialRole.TOOLCHAIN
            ):
                raise ValueError("invalid exec image generation")
            close_image(event.task, event.time_ns)
            active[event.task] = (event.image, integer(v[0]), event.time_ns)
            uses.append(
                InputUse(
                    len(uses) + 1,
                    context,
                    event.task,
                    event.image,
                    material(integer(v[0])).material_id,
                    0,
                    UseKind.EXEC_BOUND,
                    event.time_ns,
                    None,
                    None,
                    None,
                )
            )
        elif event.kind in ("READ", "MAP", "META", "FAILED", "EXIT"):
            if event.task not in active or event.image != active[event.task][0]:
                raise ValueError("wrong task/image generation at observation")
            if event.kind == "EXIT":
                close_image(event.task, event.time_ns)
                del active[event.task]
                code = integer(v[1])
                kind = ExitKind(cast(str, v[0]))
                if parents[event.task] is None:
                    root_exit = (kind, code)
                if kind is not ExitKind.EXITED or code != 0:
                    reasons.add("PAYLOAD_NOT_SUCCESSFUL")
            elif event.kind != "FAILED":
                m = material(integer(v[0]))
                offset = integer(v[1]) if event.kind != "META" else None
                length = integer(v[2]) if event.kind != "META" else None
                digest_read = None
                if offset is not None and length is not None and offset + length > UINT64_MAX:
                    raise ValueError("observed range overflow")
                if event.kind == "READ":
                    assert offset is not None and length is not None
                    if length > 0 and offset + length > m.size:
                        raise ValueError("returned bytes outside bound object")
                    digest_read = hashlib.sha256(hex_bytes(v[3], 4096)).hexdigest()
                    if offset == 0 and length == m.size and digest_read != m.sha256:
                        raise ValueError("full returned read contradicts object content")
                use_kind = {
                    "READ": UseKind.READ_BYTES,
                    "MAP": UseKind.MMAP_BOUND,
                    "META": UseKind.METADATA_ONLY,
                }[event.kind]
                uses.append(
                    InputUse(
                        len(uses) + 1,
                        context,
                        event.task,
                        event.image,
                        m.material_id,
                        0,
                        use_kind,
                        event.time_ns,
                        offset,
                        length,
                        digest_read,
                    )
                )
        elif event.kind == "ERROR":
            if (event.task == 0 and event.image != 0) or (
                event.task != 0
                and (event.task not in active or event.image != active[event.task][0])
            ):
                raise ValueError("error has unknown task/image provenance")
            reasons.add(cast(str, v[0]))
            capture_error = True
        elif event.kind != "PAYLOAD":
            raise ValueError("unsupported causal observation stage")
    end = capture.events[-1].values
    if end[1] != len(parents) or end[2] != len(materials):
        raise ValueError("capture terminal counters mismatch")
    if active:
        reasons.add("MISSING_TASK_EXIT")
    if not parents:
        reasons.add("MISSING_TASK_BIRTH")
    if end[0] and (active or not parents or capture_error):
        raise ValueError("contradictory complete observation window")
    if not end[0]:
        reasons.add("TRACE_WINDOW_INCOMPLETE")
    drops = None if end[3] is None else integer(end[3])
    if drops is None:
        reasons.add("DROP_COUNT_UNAVAILABLE")
    elif drops:
        reasons.add("TRACE_RECORDS_DROPPED")
    capture_hash = capture_digest(capture)
    completion = BuildCompletion(
        root_exit[0] if root_exit else None,
        root_exit[1] if root_exit and root_exit[0] is ExitKind.EXITED else None,
        root_exit[1] if root_exit and root_exit[0] is ExitKind.SIGNALLED else None,
        cast(bool, end[0]),
        drops,
        None,
        capture_hash,
        capture_hash,
        None,
    )
    receipt = BuildReceipt(
        profile.identity,
        tuple(materials.values()),
        tuple(images),
        tuple(uses),
        (),
        root_start,
        None if active else capture.events[-1].time_ns,
        completion,
        EvidenceKind.OBSERVED_UNTRUSTED,
    )
    return ProducedObservation(
        receipt, bool(end[0] and not active and drops == 0), tuple(reasons), capture
    )
