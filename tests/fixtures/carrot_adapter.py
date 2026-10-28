"""Explicit synthetic caller config/health; no vehicle-approved values."""

from dataclasses import replace

from cyberpilot_autotune.integrations.carrot.adapter import (
    AdapterConfig,
    CachePolicy,
    ProducerAttestation,
    SteeringPressedCapability,
)
from cyberpilot_autotune.integrations.carrot.availability import (
    INTEGRATION_MERGE,
    SCHEMA_REVISION,
    SOURCE_REVISION,
)
from cyberpilot_autotune.integrations.carrot.health import SessionToken, TopicHealthEvidence
from tests.fixtures.carrot_v2 import BASELINE, complete, context


def healthy():
    return TopicHealthEvidence(True, True, True, True, True)


def session(generation=0):
    return SessionToken(generation, f"{generation:032x}")


def config(kind="torque", *, generation=0, capacities=(3, 3, 2)):
    ctx = replace(context(kind), brand="volkswagen" if kind == "mebCurvature" else "tesla")
    _, policy = complete(kind)
    policy = replace(policy, static_context_digest=ctx.digest)
    capability = SteeringPressedCapability(
        "opendbc_repo/opendbc/car/volkswagen/carstate.py"
        if kind == "mebCurvature"
        else "opendbc_repo/opendbc/car/tesla/carstate.py",
        "CarState.update_meb" if kind == "mebCurvature" else "CarState.update",
        SOURCE_REVISION,
    )
    attestation = ProducerAttestation(
        SOURCE_REVISION,
        INTEGRATION_MERGE,
        SCHEMA_REVISION,
        ctx.digest,
        1,
        session(generation),
        (kind,),
        capability,
    )
    return AdapterConfig(ctx, policy, BASELINE, CachePolicy(*capacities), attestation)
