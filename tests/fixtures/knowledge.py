"""Synthetic descriptor metadata; not a vehicle policy or authenticated source."""

REVISION = "c2130730239bcdb4cbde9361ab90c8d99aa4ff55"


def claim(**changes):
    from cyberpilot_autotune.knowledge.contracts import Confidence, SourceKnowledgeDescriptor

    data = dict(
        schema_version=1,
        claim_id="synthetic:kp",
        parameter_ids=["LateralTorqueKpV"],
        repository="example/reference",
        exact_revision=REVISION,
        path="controller.py",
        symbol="SyntheticController.update",
        range_start=10,
        range_end=20,
        git_blob_sha="1" * 40,
        source_range_sha256="2" * 64,
        semantic_claim="Synthetic scaling description only.",
        conditions=["synthetic torque mode"],
        confidence=Confidence.PROVEN,
        schema_revision="synthetic-source-v1",
        supersedes_claim_id=None,
    )
    data.update(changes)
    return SourceKnowledgeDescriptor(**data)


def parameter(**changes):
    from cyberpilot_autotune.knowledge.contracts import (
        Classification,
        Confidence,
        OwnerRole,
        OwnershipStatus,
        ParameterDescriptor,
        StorageType,
    )

    data = dict(
        schema_version=1,
        parameter_id="LateralTorqueKpV",
        storage_key="LateralTorqueKpV",
        display_name="Synthetic proportional coefficient",
        domain="steering",
        family="torque_pid",
        classification=Classification.SAFETY_SENSITIVE,
        semantic_description="Synthetic controller coefficient, not an approved setting.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="synthetic coefficient count",
        storage_scale=0.01,
        canonical_unit="synthetic proportional coefficient",
        consumer_unit="synthetic proportional coefficient",
        consumer_transform_description="Stored count multiplied by the documented scale.",
        ui_unit_description="Synthetic catalog label only.",
        consumer_claim_ids=["synthetic:kp"],
        mode_conditions=["synthetic torque mode"],
        ui_default=10,
        ui_catalog_min=0,
        ui_catalog_max=20,
        storage_registry_default=10,
        default_sources=["synthetic descriptive catalog"],
        consumer_value_source="Synthetic caller evidence; never read here.",
        runtime_field="SyntheticController.pid.kp",
        descriptive_owner=[OwnerRole.CUSTOM_TORQUE_OVERRIDE],
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision=REVISION,
        evidence_status=Confidence.PROVEN,
        evidence_gaps=[],
    )
    data.update(changes)
    return ParameterDescriptor(**data)
