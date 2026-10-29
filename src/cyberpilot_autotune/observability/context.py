"""Immutable applied context; H6 semantics mirrored without a research import."""

from dataclasses import asdict, dataclass, fields

from .types import (
    AlignmentMethod,
    DelaySource,
    GeometryOrigin,
    OffsetSource,
    Precision,
    boolean,
    enum_value,
    real,
    require,
    sha,
    token,
    uint64,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class InstalledParameters:
    generation: int | None = None
    factor_installed: float | None = None
    friction_installed: float | None = None
    offset_installed: float | None = None
    offset_source: OffsetSource = OffsetSource.UNAVAILABLE
    source_field: str | None = None
    precision: Precision = Precision.UNKNOWN
    custom_selector: int | None = None

    def __post_init__(self) -> None:
        uint64(self.generation, optional=True)
        uint64(self.custom_selector, optional=True)
        for name in ("factor_installed", "friction_installed", "offset_installed"):
            object.__setattr__(self, name, real(getattr(self, name)))
        enum_value(self.offset_source, OffsetSource)
        enum_value(self.precision, Precision)
        require(
            self.source_field
            in {
                None,
                "torque_params.latAccelOffset",
                "liveTorqueParameters.latAccelOffsetFiltered",
                "liveTorqueParameters.latAccelOffsetRaw",
            },
            "OFFSET_SOURCE_FIELD",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class GainSnapshot:
    generation: int | None = None
    k_p: float | None = None
    k_i: float | None = None
    k_d: float | None = None
    k_f: float | None = None
    precision: Precision = Precision.UNKNOWN
    cycle_digest: str | None = None
    captured_mono_time_ns: int | None = None

    def __post_init__(self) -> None:
        uint64(self.generation, optional=True)
        sha(self.cycle_digest, optional=True)
        uint64(self.captured_mono_time_ns, optional=True)
        for name in ("k_p", "k_i", "k_d", "k_f"):
            object.__setattr__(self, name, real(getattr(self, name)))
        enum_value(self.precision, Precision)


@dataclass(frozen=True, slots=True, kw_only=True)
class AppliedGeometryContext:
    source_revision: str | None = None
    vehicle_context_digest: str | None = None
    generation: int | None = None
    applied_vm_context_id: str | None = None
    origin: GeometryOrigin = GeometryOrigin.UNAVAILABLE
    wheelbase: float | None = None
    center_to_front: float | None = None
    center_to_front_ratio: float | None = None
    stiffness_factor: float | None = None
    effective_steer_ratio: float | None = None
    steer_ratio_rate_raw: float | None = None
    steer_ratio_rate_effective: float | None = None
    custom_sr_raw: float | None = None
    custom_sr_effective: float | None = None
    precision: Precision = Precision.UNKNOWN
    requested_center_to_front_percent: int | None = None
    paramsd_target_ratio: float | None = None
    live_parameters_ratio: float | None = None

    def __post_init__(self) -> None:
        sha(self.source_revision, 40, optional=True)
        sha(self.vehicle_context_digest, optional=True)
        sha(self.applied_vm_context_id, optional=True)
        uint64(self.generation, optional=True)
        uint64(self.requested_center_to_front_percent, optional=True)
        enum_value(self.origin, GeometryOrigin)
        enum_value(self.precision, Precision)
        for item in fields(self):
            if item.name not in {
                "source_revision",
                "vehicle_context_digest",
                "generation",
                "applied_vm_context_id",
                "origin",
                "precision",
                "requested_center_to_front_percent",
            }:
                object.__setattr__(self, item.name, real(getattr(self, item.name)))


@dataclass(frozen=True, slots=True, kw_only=True)
class DelayContext:
    effective_delay_s: float | None = None
    source: DelaySource = DelaySource.UNAVAILABLE
    alignment_method: AlignmentMethod = AlignmentMethod.UNKNOWN
    alignment_version: str | None = None
    correction_count: int | None = None
    sample_pair_id: str | None = None
    values_already_aligned: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "effective_delay_s", real(self.effective_delay_s))
        enum_value(self.source, DelaySource)
        enum_value(self.alignment_method, AlignmentMethod)
        token(self.alignment_version, optional=True)
        uint64(self.correction_count, optional=True)
        sha(self.sample_pair_id, optional=True)
        boolean(self.values_already_aligned)


@dataclass(frozen=True, slots=True, kw_only=True)
class FrictionObservationContext:
    cycle_digest: str | None = None
    snapshot_time_ns: int | None = None
    installed: InstalledParameters | None = None
    gains: GainSnapshot | None = None
    geometry: AppliedGeometryContext | None = None
    delay: DelayContext | None = None

    def __post_init__(self) -> None:
        sha(self.cycle_digest, optional=True)
        uint64(self.snapshot_time_ns, optional=True)
        for name, cls in (
            ("installed", InstalledParameters),
            ("gains", GainSnapshot),
            ("geometry", AppliedGeometryContext),
            ("delay", DelayContext),
        ):
            value = getattr(self, name)
            require(value is None or type(value) is cls, "CONTEXT_TYPE")


def epoch_context(context: FrictionObservationContext) -> dict[str, object]:
    """Stable installed/applied state, not per-cycle captures or pair/candidate IDs."""
    result = asdict(context)
    result.pop("cycle_digest")
    result.pop("snapshot_time_ns")
    if result["geometry"] is not None:
        for name in (
            "requested_center_to_front_percent",
            "paramsd_target_ratio",
            "live_parameters_ratio",
        ):
            result["geometry"].pop(name)
    if result["delay"] is not None:
        result["delay"].pop("sample_pair_id")
    if result["gains"] is not None:
        result["gains"].pop("cycle_digest")
        result["gains"].pop("captured_mono_time_ns")
    return result
