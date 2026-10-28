"""Synchronous steering host transactions; rollback/readback failure is explicit."""

from collections import deque
from dataclasses import replace
from fractions import Fraction

from cyberpilot_autotune.contracts import ObservationSnapshot
from cyberpilot_autotune.contracts.validation import ValidationError, nonnegative
from cyberpilot_autotune.runtime.clock import Clock

from .contracts import (
    ApplicationReason as R,
)
from .contracts import (
    ApplicationReceipt,
    AuthorizationGrant,
    EvidenceQuality,
    SteeringPolicy,
    SteeringRequest,
    TargetSnapshot,
)
from .contracts import (
    ApplicationState as S,
)
from .ports import ApplicationAuthority, SteeringTarget


class _Reject(Exception):
    def __init__(self, reason: R, *, fault: bool = False) -> None:
        self.reason, self.fault = reason, fault


class BoundedSteeringApplicator:
    """Caller-serialized, policy-driven capability. No IO or work at construction.

    Watchdog/disarm must be invoked by the owner; synchronous callbacks cannot be
    preempted. No live Carrot owner adapter is supplied. Construct a new reviewed
    owner session after a fault; no automatic rearming or state persistence.
    """

    def __init__(
        self,
        policy: SteeringPolicy,
        baseline: TargetSnapshot,
        target: SteeringTarget,
        authority: ApplicationAuthority,
        clock: Clock,
    ) -> None:
        if type(policy) is not SteeringPolicy or type(baseline) is not TargetSnapshot:
            raise ValidationError("typed policy and trusted baseline required")
        for capability, method in (
            (target, "snapshot"),
            (target, "commit"),
            (authority, "authorize"),
            (clock, "now_s"),
        ):
            if not callable(getattr(capability, method, None)):
                raise ValidationError("explicit owner, authority and clock capabilities required")
        self._policy, self._baseline = replace(policy), replace(baseline)
        self._target, self._authority, self._clock = target, authority, clock
        self._identity(self._baseline)
        for spec in self._policy.parameters:
            value = self._baseline.values.get(spec.parameter_id)
            if value is None or not spec.lower_bound <= value <= spec.upper_bound:
                raise ValidationError("baseline absent/outside reviewed policy")
        self._state = S.READY
        self._expected = self._baseline
        self._pending: TargetSnapshot | None = None
        self._observed: TargetSnapshot | None = None
        self._last_clock: float | None = None
        self._last_sequence: int | None = None
        self._last_observation_s: float | None = None
        self._last_change_s = self._baseline.timestamp_s
        self._active_until_s: float | None = None
        self._recovery_reason: R | None = None
        self._ids: deque[str] = deque()
        self._consumed: set[str] = set()

    def _identity(self, snapshot: TargetSnapshot) -> None:
        p = self._policy
        if (
            snapshot.owner_id != p.owner_id
            or snapshot.context_digest != p.context_digest
            or snapshot.baseline_epoch != p.baseline_epoch
            or snapshot.scope is not p.scope
        ):
            raise ValidationError("target identity differs from policy")

    def _now(self) -> float:
        try:
            now = nonnegative(self._clock.now_s(), "application clock")
            if now < self._baseline.timestamp_s:
                raise ValidationError("baseline anchor is in the future")
            if self._last_clock is not None and now < self._last_clock:
                raise ValidationError("regressed application clock")
            self._last_clock = now
            return now
        except Exception:
            raise _Reject(R.CLOCK_FAULT, fault=True) from None

    def _read(self, *, recovery: bool = False) -> TargetSnapshot:
        raw = self._target.snapshot()
        if type(raw) is not TargetSnapshot:
            raise ValidationError("immutable owner snapshot required")
        state = replace(raw)
        self._identity(state)
        if set(state.values) != set(self._baseline.values):
            raise ValidationError("target tuple shape changed")
        if not recovery:
            now = self._now()
            if state.timestamp_s > now or Fraction(now) - Fraction(state.timestamp_s) > Fraction(
                self._policy.maximum_target_age_s
            ):
                raise _Reject(R.TARGET_CONFLICT, fault=True)
        self._observed = state
        return state

    @staticmethod
    def _same(left: TargetSnapshot, right: TargetSnapshot) -> bool:
        return left.revision == right.revision and left.values == right.values

    def _receipt(self, reason: R, sequence: int | None = None) -> ApplicationReceipt:
        observed = self._observed
        return ApplicationReceipt(
            reason,
            self._state,
            sequence,
            self._baseline.values,
            observed.values if observed else None,
            observed.revision if observed else None,
            self._last_clock,
            self._recovery_reason,
        )

    def _restore(self) -> bool:
        """Restore only a coherent owned revision; never overwrite a foreign state."""
        started = self._last_clock
        try:
            current = self._read(recovery=True)
            if not self._same(current, self._expected) and not (
                self._pending is not None and self._same(current, self._pending)
            ):
                raise ValidationError("owner revision cannot be proven")
            if current.values != self._baseline.values:
                try:
                    ack = self._target.commit(current.revision, self._baseline.values)
                    if type(ack) is not int or ack != current.revision + 1:
                        self._state = S.FAULTED
                        self._recovery_reason = R.TARGET_FAULT
                except Exception:
                    self._state = S.FAULTED
                    self._recovery_reason = R.TARGET_FAULT
                restored = self._read(recovery=True)
                if (
                    restored.revision != current.revision + 1
                    or restored.values != self._baseline.values
                ):
                    raise ValidationError("baseline restoration not verified")
                current = restored
            self._expected, self._pending = current, None
            self._active_until_s = None
            try:
                finished = self._now()
                if started is not None and Fraction(finished) - Fraction(started) > Fraction(
                    self._policy.maximum_rollback_s
                ):
                    self._recovery_reason = R.ROLLBACK_TIMEOUT
                    self._state = S.FAULTED
            except _Reject:
                self._recovery_reason = R.CLOCK_FAULT
                self._state = S.FAULTED
            if self._last_clock is not None:
                self._last_change_s = self._last_clock
            return True
        except Exception:
            self._observed = None
            self._state = S.FAULTED
            self._recovery_reason = R.ROLLBACK_FAILED
            return False

    def _reject(
        self, reason: R, sequence: int | None = None, *, fault: bool = False
    ) -> ApplicationReceipt:
        if fault:
            self._state = S.FAULTED
            self._observed = None
        if self._active_until_s is not None or self._pending is not None:
            if not self._restore():
                reason = R.ROLLBACK_FAILED
            elif self._state is not S.FAULTED:
                self._state = S.READY
        return self._receipt(reason, sequence)

    def _source(self, raw: object, now: float) -> ObservationSnapshot:
        if type(raw) is not ObservationSnapshot:
            raise _Reject(R.INVALID_INPUT)
        obs = replace(raw)
        if obs.context_key != self._policy.observation_context:
            raise _Reject(R.POLICY_MISMATCH, fault=True)
        if obs.baseline_parameters != self._baseline.values:
            raise _Reject(R.BASELINE_MISMATCH, fault=True)
        if obs.timestamp_s > now:
            raise _Reject(R.ORDERING, fault=True)
        if Fraction(now) - Fraction(obs.timestamp_s) + Fraction(obs.source_age_s) > Fraction(
            self._policy.maximum_source_age_s
        ):
            raise _Reject(R.STALE_SOURCE)
        if (
            obs.source_valid is not True
            or obs.speed_mps is None
            or obs.speed_mps < self._policy.minimum_speed_mps
        ):
            raise _Reject(R.SOURCE_INVALID)
        if obs.control_active is not True:
            raise _Reject(R.CONTROL_INACTIVE)
        if obs.driver_override is not False:
            raise _Reject(R.OVERRIDE)
        if obs.controller_saturated is not False:
            raise _Reject(R.SATURATED)
        return obs

    def _reserve(self, raw: object) -> tuple[SteeringRequest, int]:
        if type(raw) is not SteeringRequest:
            raise _Reject(R.INVALID_INPUT)
        sequence = raw.sequence
        if type(sequence) is not int or sequence < 0:
            raise _Reject(R.INVALID_INPUT, fault=True)
        previous = self._last_sequence
        self._last_sequence = max(sequence, previous) if previous is not None else sequence
        if previous is not None and sequence <= previous:
            raise _Reject(R.REPLAYED)
        try:
            item = replace(raw)
        except ValidationError:
            raise _Reject(R.INVALID_INPUT) from None
        # IDs encode this session's attempt counter. Eviction cannot revive an ID
        # using a new counter; source/evidence identity stays in its own digest.
        if int(item.proposal_id, 16) != sequence or item.proposal_id in self._consumed:
            raise _Reject(R.REPLAYED)
        self._consumed.add(item.proposal_id)
        self._ids.append(item.proposal_id)
        if len(self._ids) > self._policy.maximum_consumed_proposals:
            self._consumed.remove(self._ids.popleft())
        return item, sequence

    def _admit(
        self, item: SteeringRequest, now: float, previous_observation_s: float | None
    ) -> None:
        p, evidence, proposal = self._policy, item.evidence, item.proposal
        if item.session_token != p.session_token:
            raise _Reject(R.SESSION_MISMATCH, fault=True)
        if item.policy_sha256 != p.digest:
            raise _Reject(R.POLICY_MISMATCH, fault=True)
        if evidence.quality is not EvidenceQuality.INDEPENDENTLY_QUALIFIED:
            raise _Reject(R.UNQUALIFIED_EVIDENCE)
        if (
            evidence.source_revision != p.source_revision
            or evidence.context_digest != p.context_digest
        ):
            raise _Reject(R.POLICY_MISMATCH, fault=True)
        if evidence.target_revision != item.expected_revision:
            raise _Reject(R.TARGET_CONFLICT, fault=True)
        if evidence.generated_at_s > now or Fraction(now) - Fraction(
            evidence.generated_at_s
        ) > Fraction(p.maximum_evidence_age_s):
            raise _Reject(R.UNQUALIFIED_EVIDENCE)
        obs = self._source(item.observation, now)
        if obs.sequence != item.sequence or (
            previous_observation_s is not None and obs.timestamp_s <= previous_observation_s
        ):
            raise _Reject(R.ORDERING)
        if proposal.context_key != obs.context_key or proposal.timestamp_s != obs.timestamp_s:
            raise _Reject(R.POLICY_MISMATCH)
        if proposal.baseline_value != self._baseline.values.get(proposal.parameter_id):
            raise _Reject(R.BASELINE_MISMATCH)
        if proposal.sample_count < p.minimum_samples:
            raise _Reject(R.SAMPLES)
        if proposal.confidence < p.minimum_confidence:
            raise _Reject(R.CONFIDENCE)

    def _grant(self, item: SteeringRequest, now: float) -> AuthorizationGrant:
        try:
            raw = self._authority.authorize(item, self._policy, now)
        except Exception:
            raise _Reject(R.AUTHORIZATION_INVALID, fault=True) from None
        if raw is None:
            raise _Reject(R.AUTHORIZATION_DENIED)
        if type(raw) is not AuthorizationGrant:
            raise _Reject(R.AUTHORIZATION_INVALID, fault=True)
        try:
            grant = replace(raw)
        except ValidationError:
            raise _Reject(R.AUTHORIZATION_INVALID, fault=True) from None
        if (
            grant.request_sha256 != item.digest
            or grant.policy_sha256 != self._policy.digest
            or grant.evidence_sha256 != item.evidence.digest
            or grant.issued_at_s > now
            or grant.expires_at_s <= now
            or Fraction(now) - Fraction(grant.issued_at_s)
            > Fraction(self._policy.maximum_authorization_age_s)
        ):
            raise _Reject(R.AUTHORIZATION_INVALID, fault=True)
        return grant

    def _deadline(self, now: float, started: float, grant: AuthorizationGrant) -> None:
        if self._active_until_s is not None and now >= self._active_until_s:
            raise _Reject(R.HOLD_EXPIRED, fault=True)
        if now >= grant.expires_at_s or Fraction(now) - Fraction(started) > Fraction(
            self._policy.maximum_transaction_s
        ):
            raise _Reject(R.TRANSACTION_TIMEOUT, fault=True)

    def process(self, raw: object) -> ApplicationReceipt:
        self._observed = None
        self._recovery_reason = None
        if self._state in (S.FAULTED, S.DISARMED):
            return self._receipt(R.FAULT_LATCHED if self._state is S.FAULTED else R.DISARMED)
        sequence = None
        try:
            item, sequence = self._reserve(raw)
            started = self._now()
            if self._active_until_s is not None and started >= self._active_until_s:
                raise _Reject(R.HOLD_EXPIRED, fault=True)
            previous_observation_s = self._last_observation_s
            stamp = item.observation.timestamp_s
            if stamp <= started and (
                previous_observation_s is None or stamp > previous_observation_s
            ):
                self._last_observation_s = stamp
            self._admit(item, started, previous_observation_s)
            current = self._read()
            if (
                not self._same(current, self._expected)
                or current.revision != item.expected_revision
            ):
                raise _Reject(R.TARGET_CONFLICT, fault=True)
            spec = next(
                (
                    s
                    for s in self._policy.parameters
                    if s.parameter_id == item.proposal.parameter_id
                ),
                None,
            )
            if spec is None:
                raise _Reject(R.POLICY_MISMATCH)
            value = item.proposal.proposed_value
            delta = abs(Fraction(value) - Fraction(current.values[spec.parameter_id]))
            if not spec.lower_bound <= value <= spec.upper_bound:
                raise _Reject(R.OUT_OF_BOUNDS)
            if delta > Fraction(spec.maximum_step):
                raise _Reject(R.STEP_LIMIT)
            if delta > Fraction(spec.maximum_rate_per_second) * (
                Fraction(started) - Fraction(self._last_change_s)
            ):
                raise _Reject(R.RATE_LIMIT)
            grant = self._grant(item, started)
            refreshed = self._read()
            if not self._same(refreshed, current):
                raise _Reject(R.TARGET_CONFLICT, fault=True)
            current = refreshed
            before_commit = self._now()
            self._deadline(before_commit, started, grant)
            self._source(item.observation, before_commit)
            if delta == 0:
                return self._receipt(R.UNCHANGED, sequence)
            values = dict(current.values)
            values[spec.parameter_id] = value
            self._pending = replace(current, revision=current.revision + 1, values=values)
            ack = self._target.commit(current.revision, self._pending.values)
            if type(ack) is not int or ack != self._pending.revision:
                raise _Reject(R.TARGET_FAULT, fault=True)
            readback = self._read()
            if not self._same(readback, self._pending):
                raise _Reject(R.TARGET_FAULT, fault=True)
            finished = self._now()
            self._deadline(finished, started, grant)
            self._source(item.observation, finished)
            self._expected, self._pending = readback, None
            self._last_change_s = finished
            self._active_until_s = min(grant.expires_at_s, finished + self._policy.maximum_hold_s)
            self._state = S.ACTIVE
            return self._receipt(R.VERIFIED, sequence)
        except _Reject as exc:
            return self._reject(exc.reason, sequence, fault=exc.fault)
        except Exception:
            return self._reject(R.TARGET_FAULT, sequence, fault=True)

    def watchdog(self, observation: object) -> ApplicationReceipt:
        self._observed = None
        self._recovery_reason = None
        if self._state in (S.FAULTED, S.DISARMED):
            return self._receipt(R.FAULT_LATCHED if self._state is S.FAULTED else R.DISARMED)
        try:
            now = self._now()
            self._source(observation, now)
            if self._active_until_s is not None and now >= self._active_until_s:
                raise _Reject(R.HOLD_EXPIRED, fault=True)
            current = self._read()
            if not self._same(current, self._expected):
                raise _Reject(R.TARGET_CONFLICT, fault=True)
            return self._receipt(R.UNCHANGED)
        except _Reject as exc:
            return self._reject(exc.reason, fault=exc.fault)
        except Exception:
            return self._reject(R.TARGET_FAULT, fault=True)

    def disarm(self) -> ApplicationReceipt:
        self._observed = None
        self._recovery_reason = None
        if self._state is S.FAULTED:
            return self._receipt(R.FAULT_LATCHED)
        result = self._reject(
            R.DISARMED
            if self._active_until_s is None and self._pending is None
            else R.BASELINE_RESTORED
        )
        if result.state is not S.FAULTED:
            self._state = S.DISARMED
        return replace(result, state=self._state)
