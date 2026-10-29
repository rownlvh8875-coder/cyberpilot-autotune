"""Single-caller deterministic reference protocol; no Carrot/vehicle writer."""

from typing import NoReturn

from .contracts import (
    UINT64_MAX,
    AuthorityContext,
    BaselineRecord,
    CommitAck,
    ControllerMode,
    InstalledTuple,
    OwnerIdentity,
    OwnerLease,
    OwnerPolicy,
    OwnerProtocolError,
    OwnerState,
    RecoveryResult,
    TorqueOwnerSnapshot,
    TorqueParameterTuple,
    TorqueProposal,
    WatchdogInput,
    count,
    digest,
    require,
    time_value,
)
from .ports import Authority, Clock, TuplePort


class ReferenceTorqueParameterOwner:
    """Opaque logical tuple ownership, not scientific/application authorization.

    The injected authority is trusted independently; evidence hashes are not
    credentials. Caller serializes every operation. No clock/port/authority call
    occurs during construction; initialize explicitly admits a supplied baseline.
    """

    def __init__(
        self,
        identity: OwnerIdentity,
        baseline: BaselineRecord,
        policy: OwnerPolicy,
        clock: Clock,
        authority: Authority,
        port: TuplePort,
    ) -> None:
        require(
            type(identity) is OwnerIdentity
            and type(baseline) is BaselineRecord
            and type(policy) is OwnerPolicy
            and baseline.identity == identity,
            "owner inputs",
        )
        for capability, method in (
            (clock, "now_s"),
            (authority, "approve"),
            (port, "read"),
            (port, "compare_and_swap"),
        ):
            require(callable(getattr(capability, method, None)), "explicit capability required")
        self.identity, self.baseline, self.policy = identity, baseline, policy
        self._clock, self._authority, self._port = clock, authority, port
        self._expected = baseline.installed
        self._pending: InstalledTuple | None = None
        self._state = OwnerState.UNINITIALIZED
        self._last_clock: float | None = None
        self._lease: OwnerLease | None = None
        self._high_water = {binding.producer: -1 for binding in policy.producers}
        self._recovery_attempted = False
        self._recovery_forbidden = False
        self._close_after_recovery = False
        self._fault_reason: str | None = None

    @property
    def state(self) -> OwnerState:
        return self._state

    @property
    def fault_reason(self) -> str | None:
        return self._fault_reason

    def _fault(self, reason: str) -> NoReturn:
        if reason in {"FOREIGN_STATE", "INITIALIZATION_FAULT", "STOP_UNVERIFIED"}:
            self._recovery_forbidden = True
        self._state, self._fault_reason = OwnerState.FAULTED, reason
        raise OwnerProtocolError(reason)

    def _now(self, *, observe_only: bool = False) -> float:
        now = self._clock.now_s()
        time_value(now)
        if now < self.baseline.captured_at_s or (
            self._last_clock is not None and now < self._last_clock
        ):
            raise OwnerProtocolError("CLOCK_FAULT")
        if not observe_only:
            self._last_clock = now
        return now

    def _operation_time(self) -> float:
        try:
            return self._now()
        except Exception:
            self._fault("CLOCK_FAULT")

    def _read(self) -> InstalledTuple:
        raw = self._port.read()
        if type(raw) is not InstalledTuple or not (
            raw.digest == self._expected.digest
            or (self._pending is not None and raw.digest == self._pending.digest)
        ):
            raise OwnerProtocolError("FOREIGN_STATE")
        return raw

    def initialize(self) -> TorqueOwnerSnapshot:
        if self._state is not OwnerState.UNINITIALIZED:
            raise OwnerProtocolError("ALREADY_INITIALIZED")
        try:
            self._read()
            self._now()
            self._state = OwnerState.READY
            return self.snapshot()
        except Exception:
            self._fault("INITIALIZATION_FAULT")

    def snapshot(self) -> TorqueOwnerSnapshot:
        """Independent actual port read; never changes owner state or revision."""
        if self._state is OwnerState.UNINITIALIZED:
            raise OwnerProtocolError("UNINITIALIZED")
        current = self._read()
        return TorqueOwnerSnapshot(
            current.values,
            current.revision,
            self.identity,
            current.mode,
            self._now(observe_only=True),
            self._state,
            self._lease,
        )

    def _preflight(self) -> tuple[InstalledTuple, float]:
        if self._state not in (OwnerState.READY, OwnerState.OWNED):
            raise OwnerProtocolError(self._fault_reason or self._state.value)
        try:
            current = self._read()
        except Exception:
            self._fault("FOREIGN_STATE")
        try:
            now = self._now()
        except Exception:
            self._fault("CLOCK_FAULT")
        self._check_active_lease(now, installed=False)
        return current, now

    def _check_active_lease(self, now: float, *, installed: bool) -> None:
        if self._lease is not None and now >= self._lease.expires_at_s:
            self._fault_reason = "LEASE_EXPIRED"
            if installed:
                self._fault("LEASE_EXPIRED")
            self._state = OwnerState.RECOVERING
            raise OwnerProtocolError("LEASE_EXPIRED")

    def _authorize(self, grant: AuthorityContext, operation: str, now: float) -> None:
        if (
            type(grant) is not AuthorityContext
            or grant.owner_digest != self.identity.digest
            or (
                grant.operation_digest != operation
                or not grant.issued_at_s <= now < grant.expires_at_s
            )
        ):
            raise OwnerProtocolError("AUTHORITY")
        try:
            accepted = self._authority.approve(grant, now)
        except Exception:
            raise OwnerProtocolError("AUTHORITY") from None
        if accepted is not True:
            raise OwnerProtocolError("AUTHORITY")

    def _install(
        self,
        current: InstalledTuple,
        values: TorqueParameterTuple,
        mode: ControllerMode,
        commit_id: str,
        started: float,
        duration: float,
        *,
        guard_active_lease: bool,
        valid_until_s: float | None,
    ) -> CommitAck:
        if current.revision == UINT64_MAX:
            self._fault("REVISION_EXHAUSTED")
        now = self._operation_time()
        if guard_active_lease:
            self._check_active_lease(now, installed=False)
        if now - started > duration or (valid_until_s is not None and now >= valid_until_s):
            self._fault("DEADLINE")
        # Exactly one complete transition at the injected serialized boundary.
        update = InstalledTuple(
            values, current.revision + 1, self.identity.digest, mode, now, commit_id
        )
        self._pending = update
        try:
            ack_revision = self._port.compare_and_swap(current, update)
        except Exception:
            self._fault("UNCERTAIN_COMMIT")
        if type(ack_revision) is not int or ack_revision != update.revision:
            self._fault("ACK_FAULT")
        self._expected, self._pending = update, None
        finished = self._operation_time()
        if guard_active_lease:
            self._check_active_lease(finished, installed=True)
        if finished - started > duration or (
            valid_until_s is not None and finished >= valid_until_s
        ):
            self._fault("DEADLINE")
        return CommitAck(
            current.revision,
            update.revision,
            values.digest,
            self.identity,
            commit_id,
            now,
            self._state,
        )

    def commit(
        self, expected_revision: int, proposal: TorqueProposal, authority_context: AuthorityContext
    ) -> CommitAck | None:
        current, started = self._preflight()
        if type(proposal) is not TorqueProposal:
            raise OwnerProtocolError("INVALID_PROPOSAL")
        binding = next((b for b in self.policy.producers if b.producer is proposal.producer), None)
        if binding is None or binding.generation != proposal.producer_generation:
            raise OwnerProtocolError("PRODUCER_GENERATION")
        previous = self._high_water[proposal.producer]
        self._high_water[proposal.producer] = max(previous, proposal.sequence)
        if proposal.sequence <= previous or int(proposal.proposal_id, 16) != proposal.sequence:
            raise OwnerProtocolError("REPLAY")
        if self._lease is not None and proposal.producer is not self._lease.producer:
            raise OwnerProtocolError("PRODUCER_BUSY")
        if (
            proposal.source_revision != self.identity.source_revision
            or proposal.context_digest != self.identity.vehicle_context_digest
            or proposal.baseline_epoch != self.identity.baseline_epoch
        ):
            raise OwnerProtocolError("CONTEXT")
        if (
            current.mode not in binding.compatible_modes
            or proposal.required_mode is not current.mode
        ):
            raise OwnerProtocolError("UNSUPPORTED_MODE")
        if (
            type(expected_revision) is not int
            or expected_revision != current.revision
            or (proposal.observed_revision != expected_revision)
        ):
            raise OwnerProtocolError("CAS_CONFLICT")
        proposal_deadline = min(
            proposal.expires_at_s, proposal.generated_at_s + self.policy.maximum_proposal_age_s
        )
        if (
            proposal.generated_at_s > started
            or started >= proposal_deadline
            or (started - proposal.generated_at_s > self.policy.maximum_proposal_age_s)
        ):
            raise OwnerProtocolError("PROPOSAL_EXPIRED")
        if digest(proposal.candidate.lat_accel_offset) != digest(current.values.lat_accel_offset):
            raise OwnerProtocolError("OFFSET_PRESERVATION")
        self._authorize(authority_context, proposal.digest, started)
        refreshed, now = self._preflight()
        if refreshed.digest != current.digest:
            self._fault("FOREIGN_STATE")
        if (
            now - started > self.policy.maximum_transaction_s
            or now >= min(authority_context.expires_at_s, proposal_deadline)
            or now - proposal.generated_at_s > self.policy.maximum_proposal_age_s
        ):
            self._fault("DEADLINE")
        if proposal.candidate.digest == current.values.digest:
            return None
        if now + self.policy.maximum_lease_s <= now:
            raise OwnerProtocolError("LEASE_DURATION_UNREPRESENTABLE")
        ack = self._install(
            current,
            proposal.candidate,
            current.mode,
            digest(("install", self.identity.digest, current.revision + 1, proposal.digest))[:32],
            started,
            self.policy.maximum_transaction_s,
            guard_active_lease=True,
            valid_until_s=min(authority_context.expires_at_s, proposal_deadline),
        )
        finished = self._operation_time()
        self._check_active_lease(finished, installed=True)
        if finished >= min(authority_context.expires_at_s, proposal_deadline) or (
            finished - started > self.policy.maximum_transaction_s
            or finished - proposal.generated_at_s > self.policy.maximum_proposal_age_s
        ):
            self._fault("DEADLINE")
        lease_deadline = min(
            finished + self.policy.maximum_lease_s,
            authority_context.expires_at_s,
            proposal_deadline,
        )
        if lease_deadline <= finished:
            self._fault("LEASE_DURATION_UNREPRESENTABLE")
        self._lease = OwnerLease(
            ack.new_revision,
            proposal.producer,
            proposal.proposal_id,
            finished,
            lease_deadline,
            self.identity.baseline_epoch,
        )
        self._state = OwnerState.OWNED
        self._recovery_attempted = False
        return CommitAck(
            ack.prior_revision,
            ack.new_revision,
            ack.committed_digest,
            ack.owner_identity,
            ack.commit_id,
            ack.timestamp_s,
            self._state,
        )

    def rollback(self) -> RecoveryResult:
        if self._state in (OwnerState.UNINITIALIZED, OwnerState.DISARMED, OwnerState.STOPPED) or (
            self._state is OwnerState.FAULTED and self._recovery_attempted
        ):
            raise OwnerProtocolError("RECOVERY_UNAVAILABLE")
        was_faulted = self._state is OwnerState.FAULTED or self._fault_reason is not None
        self._recovery_attempted = True
        if self._recovery_forbidden:
            return RecoveryResult(None, None, False, "RECOVERY_CONTEXT_UNPROVEN", self._state, None)
        self._state = OwnerState.RECOVERING
        ack = None
        try:
            current, started = self._read(), self._now()
            if self._lease is not None and started >= self._lease.expires_at_s:
                was_faulted, self._fault_reason = True, "LEASE_EXPIRED"
            if current.mode is not self.baseline.mode:
                raise OwnerProtocolError("FOREIGN_CONTEXT")
            if current.values.digest != self.baseline.values.digest:
                commit_id = digest((self.identity.digest, "recovery", current.revision))[:32]
                ack = self._install(
                    current,
                    self.baseline.values,
                    current.mode,
                    commit_id,
                    started,
                    self.policy.maximum_rollback_s,
                    guard_active_lease=False,
                    valid_until_s=None,
                )
            readback = self.snapshot()
            if readback.values.digest != self.baseline.values.digest or (
                ack is not None and readback.revision != ack.new_revision
            ):
                raise OwnerProtocolError("READBACK_FAULT")
            finished = self._now()
            if self._lease is not None and finished >= self._lease.expires_at_s:
                was_faulted, self._fault_reason = True, "LEASE_EXPIRED"
            if finished - started > self.policy.maximum_rollback_s:
                raise OwnerProtocolError("ROLLBACK_DEADLINE")
            self._pending, self._lease = None, None
            self._state = (
                OwnerState.FAULTED
                if was_faulted
                else OwnerState.DISARMED
                if self._close_after_recovery
                else OwnerState.READY
            )
            self._recovery_attempted = was_faulted
            return RecoveryResult(
                readback.values,
                readback.revision,
                True,
                self._fault_reason or "BASELINE_RESTORED",
                self._state,
                ack,
            )
        except Exception:
            self._state, self._fault_reason = OwnerState.FAULTED, "ROLLBACK_FAILED"
            return RecoveryResult(None, None, False, "ROLLBACK_FAILED", self._state, ack)

    def watchdog(self, observation: WatchdogInput) -> RecoveryResult:
        if self._state not in (OwnerState.READY, OwnerState.OWNED, OwnerState.RECOVERING):
            return RecoveryResult(None, None, False, "DOMAIN_CLOSED", self._state, None)
        try:
            current, now = self._read(), self._now()
        except Exception:
            self._state, self._fault_reason = OwnerState.FAULTED, "OWNER_STATE_UNKNOWN"
            self._recovery_forbidden = True
            return RecoveryResult(None, None, False, self._fault_reason, self._state, None)
        expired = self._lease is not None and now >= self._lease.expires_at_s
        context_ok = type(observation) is WatchdogInput and (
            observation.source_revision == self.identity.source_revision
            and observation.context_digest == self.identity.vehicle_context_digest
            and observation.baseline_epoch == self.identity.baseline_epoch
            and observation.controller_mode is current.mode
            and observation.owner_alive
        )
        if not context_ok:
            self._recovery_forbidden = True
            self._state = OwnerState.FAULTED
            self._fault_reason = "LEASE_EXPIRED" if expired else "CONTEXT_OR_OWNER_LOST"
            return RecoveryResult(None, None, False, self._fault_reason, self._state, None)
        stale = observation.generated_at_s > now or (
            now - observation.generated_at_s > self.policy.maximum_observation_age_s
        )
        if expired or stale or not observation.active_producer_alive:
            self._fault_reason = "LEASE_EXPIRED" if expired else "WATCHDOG_FAILURE"
            self._state = OwnerState.FAULTED
            return self.rollback()
        if self._state is OwnerState.RECOVERING:
            return self.rollback()
        return RecoveryResult(
            current.values, current.revision, True, "UNCHANGED", self._state, None
        )

    def mode_transition_digest(self, mode: ControllerMode, expected_revision: int) -> str:
        require(type(mode) is ControllerMode, "mode")
        count(expected_revision)
        return digest(("mode", self.identity.digest, expected_revision, mode))

    def transition_mode(
        self, expected_revision: int, mode: ControllerMode, authority_context: AuthorityContext
    ) -> CommitAck | None:
        current, started = self._preflight()
        if type(expected_revision) is not int or expected_revision != current.revision:
            raise OwnerProtocolError("CAS_CONFLICT")
        if type(mode) is not ControllerMode or mode is ControllerMode.UNKNOWN:
            raise OwnerProtocolError("UNSUPPORTED_MODE")
        self._authorize(
            authority_context, self.mode_transition_digest(mode, expected_revision), started
        )
        refreshed, now = self._preflight()
        if refreshed.digest != current.digest or now >= authority_context.expires_at_s:
            self._fault("MODE_TRANSITION_FAULT")
        if now - started > self.policy.maximum_transaction_s:
            self._fault("DEADLINE")
        if self._state is OwnerState.OWNED:
            self._close_after_recovery, self._state = True, OwnerState.RECOVERING
            raise OwnerProtocolError("RECOVERY_REQUIRED")
        if mode is current.mode:
            return None
        ack = self._install(
            current,
            current.values,
            mode,
            digest(
                (
                    "mode",
                    self.identity.digest,
                    current.revision + 1,
                    authority_context.operation_digest,
                )
            )[:32],
            started,
            self.policy.maximum_transaction_s,
            guard_active_lease=True,
            valid_until_s=authority_context.expires_at_s,
        )
        finished = self._operation_time()
        if finished - started > self.policy.maximum_transaction_s:
            self._fault("DEADLINE")
        if finished >= authority_context.expires_at_s:
            self._fault("MODE_TRANSITION_FAULT")
        self._state = (
            OwnerState.DISARMED
        )  # New mode needs an explicitly supplied new epoch/session.
        return CommitAck(
            ack.prior_revision,
            ack.new_revision,
            ack.committed_digest,
            ack.owner_identity,
            ack.commit_id,
            ack.timestamp_s,
            self._state,
        )

    def disarm(self) -> RecoveryResult:
        result = self.rollback()
        if result.verified and self._state is not OwnerState.FAULTED:
            self._state = OwnerState.DISARMED
        return RecoveryResult(
            result.values, result.revision, result.verified, result.reason, self._state, result.ack
        )

    def stop(self) -> RecoveryResult:
        if self._state is OwnerState.DISARMED:
            try:
                snap = self.snapshot()
                if snap.values.digest != self.baseline.values.digest:
                    raise OwnerProtocolError("BASELINE_UNVERIFIED")
            except Exception:
                self._fault("STOP_UNVERIFIED")
            result = RecoveryResult(snap.values, snap.revision, True, "STOPPED", self._state, None)
        else:
            result = self.disarm()
        if result.verified and self._state is not OwnerState.FAULTED:
            self._state = OwnerState.STOPPED
        return RecoveryResult(
            result.values, result.revision, result.verified, result.reason, self._state, result.ack
        )

    def fault(self, reason: str) -> None:
        require(type(reason) is str and bool(reason), "explicit fault reason")
        self._state, self._fault_reason = OwnerState.FAULTED, reason

    def restart(
        self,
        identity: OwnerIdentity,
        baseline: BaselineRecord,
        policy: OwnerPolicy,
        port: TuplePort,
    ) -> "ReferenceTorqueParameterOwner":
        """Explicit logical handoff; never restores a dead process/controller.

        A real execution owner must establish fresh identity and a trusted new
        baseline independently, including after loss of this in-memory object.
        """
        if self._state not in (OwnerState.DISARMED, OwnerState.STOPPED, OwnerState.FAULTED):
            raise OwnerProtocolError("RESTART_REQUIRES_CLOSED_DOMAIN")
        require(
            identity.session_generation > self.identity.session_generation
            and identity.baseline_epoch > self.identity.baseline_epoch
            and identity.owner_instance_id != self.identity.owner_instance_id,
            "fresh identity/session/epoch required",
        )
        new_owner = ReferenceTorqueParameterOwner(
            identity, baseline, policy, self._clock, self._authority, port
        )
        new_owner.initialize()
        return new_owner
