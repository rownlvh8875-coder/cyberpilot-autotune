"""Synchronous parked qualification; only MappingDecision and diagnostics leave it."""

from collections.abc import Callable
from dataclasses import replace
from time import monotonic_ns

from cyberpilot_autotune.adapters.carrot_receipt_contract import MappingDecision, MappingReason

from ..adapter import CarrotReadOnlyAdapter
from ..errors import (
    CarrotDependencyUnavailable,
    CarrotInputError,
    CarrotSchemaIncompatible,
    CarrotSessionRequired,
)
from ..extraction import DecodedTopicSample
from ..health import uint64
from .config import TOPICS, SidecarConfig, SidecarError, SidecarReason, require
from .diagnostics import Diagnostics, DiagnosticSnapshot
from .source import SubMasterSource


class SidecarRunner:
    def __init__(
        self,
        config: SidecarConfig,
        source: SubMasterSource,
        *,
        clock: Callable[[], int] = monotonic_ns,
    ) -> None:
        self._source = source
        self._clock = clock
        try:
            self._config = replace(config)
            require(
                source.session == config.adapter.attestation.session, SidecarReason.SESSION_REQUIRED
            )
            self._adapter = CarrotReadOnlyAdapter(config.adapter)
            self._start = self._last_now = uint64(clock())
        except (SidecarError, CarrotDependencyUnavailable, CarrotSchemaIncompatible):
            source.close()
            raise
        except Exception:
            source.close()
            raise SidecarError(SidecarReason.RUNTIME_INVARIANT_FAULT) from None
        self._diag = Diagnostics()
        self._fault: SidecarReason | None = None
        self._closed = False

    @property
    def fault(self) -> SidecarReason | None:
        return self._fault

    def _fail(self, reason: SidecarReason) -> None:
        if self._fault is None:
            self._fault = reason
            self._diag.fault_count += 1
        self._diag.latest = None
        self._adapter.producer_restarted()
        self._source.close()

    def _now(self) -> int:
        try:
            now = uint64(self._clock())
        except Exception:
            raise SidecarError(SidecarReason.RUNTIME_INVARIANT_FAULT) from None
        require(now >= self._last_now, SidecarReason.MONOTONIC_REGRESSION)
        self._last_now = now
        return now

    def poll_once(self) -> tuple[MappingDecision, ...]:
        if self._fault is not None:
            raise SidecarError(self._fault)
        require(not self._closed, SidecarReason.SOURCE_CLOSED)
        results: list[MappingDecision] = []

        def consume(sample: DecodedTopicSample) -> None:
            require(sample.topic in TOPICS, SidecarReason.INVALID_TOPIC)
            require(
                sample.session_token == self._config.adapter.attestation.session,
                SidecarReason.SESSION_REQUIRED,
            )
            self._diag.received[sample.topic] += 1
            self._diag.healthy_count += int(sample.transport_health.healthy)
            if sample.topic == "carControl":
                self._adapter.ingest_car_control(sample)
            elif sample.topic == "carState":
                self._adapter.ingest_car_state(sample)
            else:
                try:
                    now = self._now()
                except SidecarError as clock_failure:
                    # None is an explicitly unavailable evaluation clock. The
                    # original boundary consumes the known cohort before rejecting.
                    decision = self._adapter.evaluate_car_output(
                        sample, evaluation_mono_time_ns=None
                    )
                    require(decision.snapshot is None, SidecarReason.RUNTIME_INVARIANT_FAULT)
                    self._diag.record(decision)
                    results.append(decision)
                    self._fail(clock_failure.reason)
                    return
                decision = self._adapter.evaluate_car_output(sample, evaluation_mono_time_ns=now)
                require(
                    decision.snapshot is None
                    or decision.snapshot.baseline_parameters
                    == self._config.adapter.baseline_parameters,
                    SidecarReason.RUNTIME_INVARIANT_FAULT,
                )
                self._diag.record(decision)
                results.append(decision)
                if decision.reason is MappingReason.UNSUPPORTED_VERSION:
                    self._fail(SidecarReason.SCHEMA_REVISION_MISMATCH)
                elif decision.reason is MappingReason.CONTROLLER_MISMATCH:
                    self._fail(SidecarReason.CONTROLLER_CONTEXT_MISMATCH)
                elif self._adapter.session_required:
                    self._fail(SidecarReason.SESSION_REQUIRED)

        try:
            self._now()
            self._source.poll(self._config.poll_timeout_ms, consume)
            if self._fault is None:
                self._now()
        except SidecarError as exc:
            if exc.topic is not None:
                self._diag.received[exc.topic] += 1
            if exc.topic == "carOutput":
                decision = self._adapter.reject_output_envelope()
                self._diag.record(decision)
                results.append(decision)
                self._fail(exc.reason)
                return tuple(results)
            self._fail(exc.reason)
            raise
        except CarrotSessionRequired:
            self._fail(SidecarReason.SESSION_REQUIRED)
            raise SidecarError(SidecarReason.SESSION_REQUIRED) from None
        except Exception:
            self._fail(SidecarReason.RUNTIME_INVARIANT_FAULT)
            raise SidecarError(SidecarReason.RUNTIME_INVARIANT_FAULT) from None
        return tuple(results)

    def producer_restarted(self) -> None:
        self._fail(SidecarReason.PRODUCER_RESTARTED)

    def new_session(self, config: SidecarConfig, source: SubMasterSource) -> None:
        try:
            candidate = replace(config)
            require(source is not self._source, SidecarReason.SESSION_REQUIRED)
            require(
                source.session == candidate.adapter.attestation.session,
                SidecarReason.SESSION_REQUIRED,
            )
            now = uint64(self._clock())
            self._adapter.reset_session(candidate.adapter)
        except (SidecarError, CarrotInputError):
            source.close()
            self._fail(SidecarReason.SESSION_REQUIRED)
            raise SidecarError(SidecarReason.SESSION_REQUIRED) from None
        except Exception:
            source.close()
            self._fail(SidecarReason.RUNTIME_INVARIANT_FAULT)
            raise SidecarError(SidecarReason.RUNTIME_INVARIANT_FAULT) from None
        self._source.close()
        self._source = source
        self._config = candidate
        self._diag = Diagnostics()
        self._start = self._last_now = now
        self._closed = False
        self._fault = None

    def diagnostics(self) -> DiagnosticSnapshot:
        cc, cs = self._adapter.cache_metrics
        latest = self._diag.latest
        snapshot = latest.snapshot if latest is not None else None
        return DiagnosticSnapshot(
            uptime_s=(self._last_now - self._start) / 1e9,
            session_state="faulted"
            if self._fault is not None
            else "closed"
            if self._closed
            else "running",
            received_counts=tuple(self._diag.received.items()),
            healthy_transport_count=self._diag.healthy_count,
            receipt_attempt_count=self._adapter.next_sequence,
            accepted_mapping_count=self._diag.accepted_count,
            rejection_counts=tuple(sorted(self._diag.rejections.items())),
            duplicate_cohort_count=self._diag.rejections["DUPLICATE_COHORT"],
            poisoned_key_count=cc.poisoned_key_count + cs.poisoned_key_count,
            cc_eviction_count=cc.eviction_count,
            cs_eviction_count=cs.eviction_count,
            session_fault_count=self._diag.fault_count,
            latest_cohort_key=latest.cohort_key if latest is not None else None,
            latest_control_active=latest.control_active if latest is not None else None,
            latest_controller_saturated=latest.controller_saturated if latest is not None else None,
            latest_source_valid=snapshot.source_valid if snapshot is not None else None,
            latest_snapshot_available=snapshot is not None,
            fault_reason=self._fault.code if self._fault is not None else None,
        )

    def close(self) -> None:
        self._source.close()
        self._closed = True
