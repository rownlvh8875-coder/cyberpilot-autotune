"""Synthetic application targets/policies: no relationship to vehicle tuning."""

from dataclasses import replace

from cyberpilot_autotune.application.contracts import (
    ApplicationScope,
    AuthorizationGrant,
    EvidenceQuality,
    SteeringEvidence,
    SteeringPolicy,
    SteeringRequest,
    TargetSnapshot,
)
from cyberpilot_autotune.contracts import ObservationSnapshot, ParameterSpec, TuningProposal


class Clock:
    def __init__(self):
        self.time = 1.0

    def now_s(self):
        return self.time


def policy(**changes):
    data = dict(
        scope=ApplicationScope.SYNTHETIC_TEST_ONLY,
        owner_id="synthetic-owner",
        source_revision="a" * 40,
        context_digest="b" * 64,
        observation_context="synthetic-steering-only",
        baseline_epoch=0,
        session_token="c" * 32,
        parameters=(
            ParameterSpec(
                "lat_accel_factor",
                "synthetic.not_for_vehicle",
                0,
                20,
                2,
                1,
                "synthetic test-only specification",
                False,
            ),
        ),
        minimum_samples=2,
        minimum_confidence=0.5,
        minimum_speed_mps=0.0,
        maximum_source_age_s=1.0,
        maximum_target_age_s=1.0,
        maximum_evidence_age_s=5.0,
        maximum_authorization_age_s=1.0,
        maximum_transaction_s=0.25,
        maximum_rollback_s=0.25,
        maximum_hold_s=2.0,
        maximum_consumed_proposals=2,
    )
    data.update(changes)
    return SteeringPolicy(**data)


def baseline(p):
    return TargetSnapshot(
        0,
        0.0,
        p.owner_id,
        p.context_digest,
        p.baseline_epoch,
        p.scope,
        {"lat_accel_factor": 10.0, "friction": 0.5, "lat_accel_offset": 0.0},
    )


class MemoryTarget:
    """Atomic synthetic CAS reference implementation, confined to tests."""

    def __init__(self, clock, state):
        self.clock = clock
        self.current = state
        self.reads = 0
        self.writes = []
        self.failure = None

    def snapshot(self):
        self.reads += 1
        if self.failure == "read" or (self.failure == "post_read" and self.writes):
            raise RuntimeError("SECRET_TARGET")
        return replace(self.current, timestamp_s=self.clock.time)

    def commit(self, expected_revision, values):
        self.writes.append((expected_revision, dict(values)))
        if expected_revision != self.current.revision or self.failure == "before_write":
            raise RuntimeError("CAS_NOT_COMMITTED")
        data = dict(values)
        if self.failure == "partial":
            data["friction"] += 0.1
        self.current = replace(
            self.current, revision=expected_revision + 1, timestamp_s=self.clock.time, values=data
        )
        if self.failure == "after_write":
            self.failure = None
            raise RuntimeError("UNCERTAIN_COMMIT")
        if self.failure == "slow":
            self.failure = None
            self.clock.time += 0.5
        return self.current.revision if self.failure != "bad_ack" else True


class Authority:
    """Synthetic trusted authority; no production allow-all implementation exists."""

    def __init__(self):
        self.calls = 0
        self.reject = False
        self.callback = None

    def authorize(self, request, policy, now_s):
        self.calls += 1
        if self.callback is not None:
            return self.callback(request, policy, now_s)
        if self.reject:
            return None
        return AuthorizationGrant(
            f"{request.sequence:032x}",
            request.digest,
            policy.digest,
            request.evidence.digest,
            now_s,
            now_s + 0.5,
        )


def request(p, *, sequence=0, now=1.0, value=11.0, revision=0, quality=None):
    b = baseline(p)
    obs = ObservationSnapshot(
        now,
        sequence,
        0.0,
        p.observation_context,
        True,
        10.0,
        0.01,
        0.01,
        None,
        False,
        False,
        b.values,
        control_active=True,
    )
    proposal = TuningProposal(
        "lat_accel_factor",
        10.0,
        value,
        0.9,
        10,
        p.observation_context,
        "synthetic-not-for-vehicle",
        now,
        (),
    )
    evidence = SteeringEvidence(
        quality or EvidenceQuality.INDEPENDENTLY_QUALIFIED,
        "d" * 64,
        p.source_revision,
        p.context_digest,
        revision,
        now,
        "synthetic",
    )
    return SteeringRequest(
        sequence, f"{sequence:032x}", p.digest, p.session_token, revision, proposal, obs, evidence
    )
