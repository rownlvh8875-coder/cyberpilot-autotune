"""Independent source-equation oracle. Never imports candidates/q helpers/NumPy."""

import random
from dataclasses import dataclass, replace

from .contracts import Sample, SteeringGeometryContext, finite, require


@dataclass(frozen=True, slots=True)
class Scenario:
    factor: float = 2.4
    friction: float = 0.17
    offset: float = 0.04
    deadzone: float = 0.06
    threshold: float = 0.3
    state: str = "symmetric"
    negative_friction: float | None = None
    compensation: bool = True
    pid_gain: float = 0.0
    u_noise: float = 0.0
    a_noise: float = 0.0
    q_noise: float = 0.0
    delay_samples: int = 0
    roll_mismatch: float = 0.0
    context_change: str = "none"
    saturated: bool = False
    override: bool = False
    count: int = 360
    seed: int = 606

    def __post_init__(self) -> None:
        require(finite(self.factor) and self.factor > 0, "FACTOR")
        require(finite(self.threshold) and self.threshold > 0, "THRESHOLD")
        for value in (self.friction, self.deadzone, self.u_noise, self.a_noise, self.q_noise):
            require(finite(value) and value >= 0, "NONNEGATIVE_SCENARIO")
        require(
            self.negative_friction is None
            or (finite(self.negative_friction) and self.negative_friction >= 0),
            "NEGATIVE_BRANCH_FRICTION",
        )
        require(
            all(finite(v) for v in (self.offset, self.pid_gain, self.roll_mismatch)),
            "SCENARIO_NUMBER",
        )
        require(
            self.state
            in {
                "symmetric",
                "asymmetric",
                "positive",
                "deadzone",
                "collinear",
                "transition",
                "correlated",
            },
            "STATE",
        )
        require(self.context_change in {"none", "geometry", "mode"}, "CONTEXT_CHANGE")
        require(type(self.count) is int and 3 <= self.count <= 12000, "COUNT")
        require(type(self.delay_samples) is int and 0 <= self.delay_samples < self.count, "DELAY")
        require(type(self.seed) is int, "SEED")
        require(
            all(type(v) is bool for v in (self.compensation, self.saturated, self.override)),
            "SCENARIO_FLAG",
        )


def generate(
    s: Scenario, context: SteeringGeometryContext, acceleration: tuple[float, ...] | None = None
) -> tuple[Sample, ...]:
    require(type(s) is Scenario and type(context) is SteeringGeometryContext, "GENERATOR_INPUT")
    require(
        acceleration is None
        or (
            type(acceleration) is tuple
            and len(acceleration) == s.count
            and all(finite(a) for a in acceleration)
        ),
        "ACCELERATION_SERIES",
    )
    rng = random.Random(s.seed)
    result = []
    outputs = []
    for i in range(s.count):
        error = (-0.6, -0.15, 0.0, 0.15, 0.6)[i % 5]
        if s.state == "asymmetric":
            error = -0.6 if i % 7 == 0 else 0.6
        elif s.state == "positive":
            error = 0.6
        elif s.state == "deadzone":
            error = 0.01
        elif s.state == "transition":
            error = (-0.15, 0.15)[i % 2]
        # Source center deadzone ZEROES strictly interior values; it does not subtract width.
        centered = 0.0 if -s.deadzone < error < s.deadzone else error
        q_true = max(-1.0, min(1.0, centered / s.threshold)) if s.compensation else 0.0
        desired = ((i * 37) % 101 - 50) / 20.0
        roll = 0.02
        actual = desired - error
        # Explicit desired/actual construction, not a sign(a) surrogate for q.
        a = desired - roll if acceleration is None else acceleration[i]
        if s.state == "collinear":
            a = q_true
        elif s.state == "correlated":
            a += 1.2 * (desired - actual)
        c = s.friction if q_true >= 0 or s.negative_friction is None else s.negative_friction
        term = c * q_true
        raw = a / s.factor + term + s.offset
        outputs.append(raw)
        pid = s.pid_gain * (0.23 * q_true + 0.05 * a)
        total = raw + pid
        if s.saturated:
            total = max(-0.3, min(0.3, total))
        ctx = context
        if i >= s.count // 2 and s.context_change == "geometry":
            require(
                context.wheelbase is not None and context.center_to_front_ratio is not None,
                "GEOMETRY_ORACLE_CONTEXT",
            )
            assert context.wheelbase is not None and context.center_to_front_ratio is not None
            ratio = context.center_to_front_ratio + 0.01
            ctx = replace(
                context,
                center_to_front_ratio=ratio,
                center_to_front=context.wheelbase * ratio,
                geometry_generation=(context.geometry_generation or 0) + 1,
            )
        elif i >= s.count // 2 and s.context_change == "mode":
            ctx = replace(context, controller_mode="NN")
        observed_u = outputs[max(0, i - s.delay_samples)] + s.u_noise * (rng.random() * 2 - 1)
        observed_a = a + s.a_noise * (rng.random() * 2 - 1) + s.roll_mismatch * q_true
        observed_q = max(-1.0, min(1.0, q_true + s.q_noise * (rng.random() * 2 - 1)))
        result.append(
            Sample(
                observed_a,
                observed_u,
                observed_q,
                term,
                pid,
                total,
                ctx,
                1000 + i * 10000000,
                s.saturated,
                s.override,
            )
        )
    return tuple(result)
