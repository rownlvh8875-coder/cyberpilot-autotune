"""Pure mutual-consistency checking, never execution or promotion eligibility."""

from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum

from .codec import receipt_digest
from .models import (
    CLOCK_DOMAIN,
    UINT64_MAX,
    BuildMaterial,
    BuildReceipt,
    ExitKind,
    MaterialRole,
    PromotionReceipt,
    TaskImage,
    UseKind,
    records,
    uint,
)

EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
BLOCKERS = (
    "BUILD_CONSUMPTION_PRODUCER_NOT_IMPLEMENTED",
    "INPUT_SEAL_BACKEND_UNQUALIFIED",
    "OUTPUT_PROMOTION_BACKEND_UNQUALIFIED",
    "EXTERNAL_EXECUTOR_UNQUALIFIED",
    "RECEIPT_AUTHENTICITY_UNQUALIFIED",
    "GUEST_FULL_INPUT_CLOSURE_UNQUALIFIED",
    "APPLICATION_NOT_AUTHORIZED",
)


class ReceiptStatus(StrEnum):
    CONSISTENT = "DIAGNOSTIC_CHAIN_CONSISTENT"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class ReceiptDecision:
    status: ReceiptStatus
    reasons: tuple[str, ...]
    read_events: int
    map_bindings: int
    exec_bindings: int
    metadata_events: int
    promotions_checked: int
    overall_status: str = field(default="BLOCKED", init=False)
    blockers: tuple[str, ...] = field(default=BLOCKERS, init=False)
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
        if type(self.status) is not ReceiptStatus:
            raise ValueError("unsupported diagnostic status")
        reasons = tuple(self.reasons)
        if any(type(reason) is not str or not reason for reason in reasons):
            raise ValueError("invalid diagnostic reasons")
        if (self.status is ReceiptStatus.CONSISTENT) != (not reasons):
            raise ValueError("inconsistent diagnostic status")
        for count in (
            self.read_events,
            self.map_bindings,
            self.exec_bindings,
            self.metadata_events,
            self.promotions_checked,
        ):
            uint(count)
        object.__setattr__(self, "reasons", tuple(sorted(set(reasons))))


def _inside(start: int | None, finish: int | None, time: int) -> bool:
    return start is not None and finish is not None and start <= time <= finish


def _materials(build: BuildReceipt, reasons: set[str]) -> dict[tuple[str, int], BuildMaterial]:
    result = {(m.material_id, m.generation): m for m in build.materials}
    if not result:
        reasons.add("MATERIALS_MISSING")
    if len({m.material_id for m in build.materials}) != len(build.materials):
        reasons.add("MATERIAL_ID_REUSED")
    cohorts = {
        MaterialRole.SOURCE: build.identity.source_digest,
        MaterialRole.TOOLCHAIN: build.identity.toolchain_digest,
        MaterialRole.CONFIG: build.identity.environment_digest,
    }
    for material in build.materials:
        if material.role is MaterialRole.GENERATED:
            reasons.add("GENERATED_INPUT_CHAIN_UNSUPPORTED")
        else:
            expected = cohorts[material.role]
            if expected is not None and expected != material.cohort_digest:
                reasons.add("MATERIAL_COHORT_MISMATCH")
            if material.origin_digest is not None:
                reasons.add("UNEXPECTED_MATERIAL_ORIGIN")
        if material.size == 0 and material.sha256 != EMPTY_SHA:
            reasons.add("EMPTY_MATERIAL_HASH_MISMATCH")
    return result


def _images(
    build: BuildReceipt, materials: dict[tuple[str, int], BuildMaterial], reasons: set[str]
) -> dict[tuple[int, int], TaskImage]:
    result = {(i.task_generation, i.exec_generation): i for i in build.images}
    groups: dict[int, list[TaskImage]] = defaultdict(list)
    for image in build.images:
        groups[image.task_generation].append(image)
        if (
            image.start_ns > image.finish_ns
            or not _inside(build.start_ns, build.finish_ns, image.start_ns)
            or not _inside(build.start_ns, build.finish_ns, image.finish_ns)
        ):
            reasons.add("IMAGE_TIME_INVALID")
        material = materials.get((image.image_id, image.image_generation))
        if material is None:
            reasons.add("IMAGE_MATERIAL_UNKNOWN")
        elif material.role is not MaterialRole.TOOLCHAIN:
            reasons.add("IMAGE_ROLE_INVALID")
    if not result:
        reasons.add("TASK_IMAGES_MISSING")
    parents: dict[int, int | None] = {}
    for task, images in groups.items():
        parents[task] = images[0].parent_generation
        if len({image.parent_generation for image in images}) != 1:
            reasons.add("TASK_PARENT_CHANGED")
        if [image.exec_generation for image in images] != list(range(len(images))):
            reasons.add("EXEC_GENERATION_GAP")
        if any(a.finish_ns > b.start_ns for a, b in zip(images, images[1:], strict=False)):
            reasons.add("IMAGE_INTERVAL_OVERLAP")
    if sum(parent is None for parent in parents.values()) != 1:
        reasons.add("MULTIPLE_TASK_ROOTS")
    processed: set[int] = set()
    for task in parents:
        trail: set[int] = set()
        current: int | None = task
        while current is not None and current not in processed:
            if current in trail:
                reasons.add("TASK_LINEAGE_CYCLE")
                break
            if current not in parents:
                reasons.add("TASK_PARENT_UNKNOWN")
                break
            trail.add(current)
            current = parents[current]
        processed.update(trail)
        parent = parents[task]
        if (
            parent is not None
            and parent in groups
            and not any(
                _inside(image.start_ns, image.finish_ns, groups[task][0].start_ns)
                for image in groups[parent]
            )
        ):
            reasons.add("CHILD_BIRTH_OUTSIDE_PARENT_IMAGE")
    return result


def evaluate_receipts(
    build: BuildReceipt, promotions: tuple[PromotionReceipt, ...]
) -> ReceiptDecision:
    build.__post_init__()
    claims = records(promotions, PromotionReceipt)
    reasons: set[str] = set()
    identity = build.identity
    for name in ("source", "toolchain", "recipe", "environment", "observer"):
        if getattr(identity, name + "_digest") is None:
            reasons.add("MISSING_" + name.upper() + "_COHORT")
    if identity.clock_domain != CLOCK_DOMAIN:
        reasons.add("WRONG_CLOCK_DOMAIN")
    if build.start_ns is None or build.finish_ns is None:
        reasons.add("MISSING_BUILD_INTERVAL")
    elif build.start_ns > build.finish_ns:
        reasons.add("BUILD_TIME_ORDER_INVALID")
    materials = _materials(build, reasons)
    images = _images(build, materials, reasons)
    context_digest = receipt_digest(identity)
    read = maps = execs = metadata = 0
    previous_time = 0
    if not build.uses:
        reasons.add("CONSUMPTION_STREAM_MISSING")
    for sequence, use in enumerate(build.uses, 1):
        if use.sequence != sequence:
            reasons.add("SEQUENCE_INVALID")
        if use.time_ns < previous_time:
            reasons.add("USE_TIME_ORDER_INVALID")
        previous_time = use.time_ns
        if use.context_digest != context_digest:
            reasons.add("USE_CONTEXT_MISMATCH")
        material = materials.get((use.material_id, use.material_generation))
        image = images.get((use.task_generation, use.exec_generation))
        if material is None:
            reasons.add("MATERIAL_UNKNOWN")
        if image is None:
            reasons.add("TASK_IMAGE_UNKNOWN")
        elif not _inside(image.start_ns, image.finish_ns, use.time_ns):
            reasons.add("USE_OUTSIDE_IMAGE")
        if not _inside(build.start_ns, build.finish_ns, use.time_ns):
            reasons.add("USE_OUTSIDE_BUILD")
        if use.kind is UseKind.READ_BYTES:
            read += 1
            if use.offset is None or use.length is None:
                reasons.add("MISSING_READ_RANGE")
            else:
                if use.offset + use.length > UINT64_MAX:
                    reasons.add("RANGE_OVERFLOW")
                if material is not None:
                    if use.length > 0 and use.offset + use.length > material.size:
                        reasons.add("READ_OUTSIDE_MATERIAL")
                    if (
                        use.offset == 0
                        and use.length == material.size
                        and use.range_digest is not None
                        and use.range_digest != material.sha256
                    ):
                        reasons.add("FULL_READ_HASH_MISMATCH")
                if (
                    use.length == 0
                    and use.range_digest is not None
                    and use.range_digest != EMPTY_SHA
                ):
                    reasons.add("EMPTY_READ_HASH_MISMATCH")
            if use.range_digest is None:
                reasons.add("MISSING_READ_DIGEST")
        elif use.kind is UseKind.MMAP_BOUND:
            maps += 1
            if use.offset is None or use.length is None:
                reasons.add("MISSING_MAP_EXTENT")
            elif use.length == 0:
                reasons.add("INVALID_MAP_EXTENT")
            elif use.offset + use.length > UINT64_MAX:
                reasons.add("RANGE_OVERFLOW")
            if use.range_digest is not None:
                reasons.add("MMAP_HAS_READ_HASH")
        else:
            if use.kind is UseKind.EXEC_BOUND:
                execs += 1
                if image is not None and (use.material_id, use.material_generation) != (
                    image.image_id,
                    image.image_generation,
                ):
                    reasons.add("EXEC_OBJECT_MISMATCH")
                reason = "EXEC_HAS_BYTE_CLAIM"
            else:
                metadata += 1
                reason = "METADATA_HAS_BYTE_CLAIM"
            if use.offset is not None or use.length is not None or use.range_digest is not None:
                reasons.add(reason)
    completion = build.completion
    if completion.sequence_complete is None:
        reasons.add("TRACE_SEQUENCE_UNAVAILABLE")
    elif not completion.sequence_complete:
        reasons.add("DECLARED_TRACE_INCOMPLETE")
    if completion.dropped_events is None:
        reasons.add("MISSING_DROP_COUNT")
    elif completion.dropped_events:
        reasons.add("TRACE_DROPPED")
    for name, reason in (
        ("input_seal_digest", "MISSING_INPUT_SEAL_WITNESS"),
        ("task_trace_digest", "MISSING_TASK_TRACE_WITNESS"),
        ("input_trace_digest", "MISSING_CONSUMPTION_TRACE_WITNESS"),
        ("writer_trace_digest", "MISSING_WRITER_TRACE_WITNESS"),
    ):
        if getattr(completion, name) is None:
            reasons.add(reason)
    if (
        completion.exit_kind is None
        or (completion.exit_kind is ExitKind.EXITED and completion.exit_code is None)
        or (completion.exit_kind is ExitKind.SIGNALLED and completion.term_signal is None)
    ):
        reasons.add("MISSING_EXIT_STATUS")
    elif completion.exit_kind is not ExitKind.EXITED or completion.exit_code != 0:
        reasons.add("BUILD_NOT_SUCCESSFUL")
    outputs = {(o.output_id, o.generation): o for o in build.outputs}
    if not outputs:
        reasons.add("OUTPUT_MISSING")
    if len({o.output_id for o in build.outputs}) != len(build.outputs):
        reasons.add("OUTPUT_ID_REUSED")
    for output in build.outputs:
        if any(output.output_id == m.material_id for m in build.materials):
            reasons.add("OUTPUT_ALIASES_INPUT")
        image = images.get((output.writer_task_generation, output.writer_exec_generation))
        if image is None:
            reasons.add("OUTPUT_WRITER_UNKNOWN")
        if output.last_write_ns is None:
            reasons.add("MISSING_OUTPUT_WRITE_TIME")
        else:
            if not _inside(build.start_ns, build.finish_ns, output.last_write_ns):
                reasons.add("OUTPUT_WRITE_OUTSIDE_BUILD")
            if image is not None and not _inside(
                image.start_ns, image.finish_ns, output.last_write_ns
            ):
                reasons.add("OUTPUT_WRITE_OUTSIDE_IMAGE")
        if output.size == 0 and output.sha256 != EMPTY_SHA:
            reasons.add("EMPTY_OUTPUT_HASH_MISMATCH")
    seen: set[tuple[str, int]] = set()
    build_digest = receipt_digest(build)
    for claim in claims:
        key = (claim.output_id, claim.output_generation)
        if key in seen:
            reasons.add("DUPLICATE_PROMOTION")
        seen.add(key)
        if claim.context_digest != context_digest:
            reasons.add("PROMOTION_CONTEXT_MISMATCH")
        if claim.build_digest != build_digest:
            reasons.add("PROMOTION_BUILD_MISMATCH")
        promoted_output = outputs.get(key)
        if promoted_output is None:
            reasons.add("UNKNOWN_PROMOTED_OUTPUT")
        elif claim.output_sha256 != promoted_output.sha256:
            reasons.add("PROMOTED_OUTPUT_HASH_MISMATCH")
        if claim.staged_sha256 is None or claim.sealed_sha256 is None:
            reasons.add("MISSING_PROMOTION_HASH")
        if promoted_output is not None and any(
            d is not None and d != promoted_output.sha256
            for d in (claim.staged_sha256, claim.sealed_sha256)
        ):
            reasons.add("OUTPUT_MUTATED")
        if claim.source_namespace_digest is None or claim.destination_namespace_digest is None:
            reasons.add("MISSING_NAMESPACE_BINDING")
        elif claim.source_namespace_digest == claim.destination_namespace_digest:
            reasons.add("NAMESPACE_ALIAS")
        for value, reason in (
            (claim.quiescence_digest, "MISSING_QUIESCENCE_WITNESS"),
            (claim.seal_digest, "MISSING_OUTPUT_SEAL_WITNESS"),
            (claim.verification_digest, "MISSING_INDEPENDENT_VERIFICATION"),
        ):
            if value is None:
                reasons.add(reason)
        times = (
            promoted_output.last_write_ns if promoted_output is not None else None,
            build.finish_ns,
            claim.quiesced_ns,
            claim.sealed_ns,
            claim.verified_ns,
            claim.promoted_ns,
        )
        available = [t for t in times if t is not None]
        if len(available) != len(times):
            reasons.add("MISSING_PROMOTION_TIMING")
        elif available != sorted(available):
            reasons.add("PROMOTION_TIME_ORDER_INVALID")
    if outputs.keys() - seen:
        reasons.add("MISSING_PROMOTION")
    return ReceiptDecision(
        ReceiptStatus.REJECTED if reasons else ReceiptStatus.CONSISTENT,
        tuple(sorted(reasons)),
        read,
        maps,
        execs,
        metadata,
        len(claims),
    )
