"""Independent controller-equation oracle, never imports a fit or analytic helper."""

from dataclasses import asdict, dataclass
from math import sin
from random import Random

from .contracts import Point, digest, number, require


@dataclass(frozen=True, slots=True)
class SyntheticScenario:
    name: str
    factor: float
    controller_friction: float
    offset: float
    commands: tuple[float, ...]
    errors: tuple[float, ...]
    deadzone: float
    friction_threshold: float
    x_noise_std: float
    y_noise_std: float
    lag_steps: int
    alignment_steps: int
    roll_bias_rad: tuple[float, ...]
    nonlinear_gain: float
    sample_group_size: int
    seed: int

    def __post_init__(self) -> None:
        require(type(self.name) is str and bool(self.name), "SCENARIO_NAME")
        require(
            all(
                number(v)
                for v in (
                    self.factor,
                    self.controller_friction,
                    self.offset,
                    self.deadzone,
                    self.friction_threshold,
                    self.x_noise_std,
                    self.y_noise_std,
                    self.nonlinear_gain,
                )
            ),
            "FINITE_MODEL_REQUIRED",
        )
        require(
            self.factor > 0
            and self.friction_threshold > 0
            and min(self.controller_friction, self.deadzone, self.x_noise_std, self.y_noise_std)
            >= 0,
            "MODEL_DOMAIN",
        )
        require(type(self.commands) is tuple and len(self.commands) >= 3, "TRAJECTORY")
        require(
            all(
                type(v) is tuple and len(v) == len(self.commands) and all(number(x) for x in v)
                for v in (self.commands, self.errors, self.roll_bias_rad)
            ),
            "TRAJECTORY",
        )
        require(
            all(type(v) is int and v >= 0 for v in (self.lag_steps, self.alignment_steps))
            and max(self.lag_steps, self.alignment_steps) <= len(self.commands) - 3,
            "LAG_DOMAIN",
        )
        require(
            type(self.sample_group_size) is int
            and self.sample_group_size > 0
            and type(self.seed) is int,
            "GROUP_OR_SEED",
        )


@dataclass(frozen=True, slots=True)
class SyntheticData:
    points: tuple[Point, ...]
    groups: tuple[int, ...]
    scenario_digest: str


def generate(case: SyntheticScenario) -> SyntheticData:
    require(type(case) is SyntheticScenario, "SCENARIO_REQUIRED")
    rng = Random(case.seed)
    binding = digest(asdict(case))
    points = []
    groups = []
    start = max(case.lag_steps, case.alignment_steps)
    for i in range(start, len(case.commands)):
        source = i - case.lag_steps
        error = case.errors[source]
        # Independently encode the actual center-deadzone / interpolation model.
        state = 0.0 if -case.deadzone < error < case.deadzone else error / case.friction_threshold
        friction = case.controller_friction * min(1.0, max(-1.0, state))
        command = case.commands[source]
        acceleration = case.factor * (command - friction) + case.offset
        acceleration += case.nonlinear_gain * command**3
        acceleration -= 9.81 * sin(case.roll_bias_rad[i])
        x = case.commands[i - case.alignment_steps] + rng.gauss(0.0, case.x_noise_std)
        y = acceleration + rng.gauss(0.0, case.y_noise_std)
        points.append(Point(digest((binding, i)), i * 1_000_000, x, y))
        groups.append((i - start) // case.sample_group_size)
    return SyntheticData(tuple(points), tuple(groups), binding)
