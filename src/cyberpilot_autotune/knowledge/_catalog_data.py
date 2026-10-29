"""Audited immutable descriptive data; generated from independent H2 source review.

No reference source bodies, IO, current values, policies or conversion routines.
"""

from .contracts import (
    Classification,
    Confidence,
    KnowledgeRegistry,
    OwnerRole,
    OwnershipStatus,
    ParameterDescriptor,
    SourceKnowledgeDescriptor,
    StorageType,
)

HOYA_CLAIMS: tuple[SourceKnowledgeDescriptor, ...] = (
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:controlsd-live",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/controls/controlsd.py",
        symbol="Controls.state_control",
        range_start=122,
        range_end=126,
        git_blob_sha="d0adba6a80659424a907683d14d8292475ced76b",
        source_range_sha256=("4243e06bf84c65290ff8e710ebd5997385a9c16cee62956df0769fa241f3c612"),
        semantic_claim=(
            "The liveTorqueParameters factorFiltered, offsetFiltered and "
            "frictionCoefficientFiltered are passed to the lateral torque "
            "setter after all_checks and useParams. No descriptive claim "
            "proves writer exclusivity."
        ),
        conditions=("SubMaster all_checks and useParams pass", "Torque lateral tuning selected"),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:custom",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.update",
        range_start=144,
        range_end=162,
        git_blob_sha="10c93b526fee645cba9dc1a6442ed118bf9eeff9",
        source_range_sha256=("55f7a8e7862b0ac88021ea905ff1e96b14e3fd2ad30aa81e039898b81da8c99a"),
        semantic_claim=(
            "A positive sampled custom mode assigns stored factor/friction "
            "times 0.001 and Kp/Ki/Kf times 0.01; it preserves the captured "
            "default offset. The prior cached mode also controls live "
            "updates."
        ),
        conditions=(
            "CP lateral tuning is torque",
            "Custom Params branch sampled every ten controller frames",
        ),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:delay",
        parameter_ids=("SteerActuatorDelay",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/controls/controlsd.py",
        symbol="Controls.state_control",
        range_start=171,
        range_end=176,
        git_blob_sha="d0adba6a80659424a907683d14d8292475ced76b",
        source_range_sha256=("88c50cf45e27d50b7444adc07208e6ff0cd107cd9a7b7e08c8fb25d1ace4d764"),
        semantic_claim=(
            "The stored delay is converted by 0.01 seconds and a zero "
            "result selects liveDelay in this controlsd path. The path is "
            "unconditional here in historical Hoya but lane-plan/active "
            "conditional in runtime/current upstream."
        ),
        conditions=(
            "Keep source-specific control-flow guard",
            "Not a measured actuator delay or guaranteed response",
        ),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:delay-model",
        parameter_ids=("SteerActuatorDelay",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/modeld/modeld.py",
        symbol="modeld_thread",
        range_start=504,
        range_end=507,
        git_blob_sha="e4de3eb2236f6bb0c54c87666099147311602f4f",
        source_range_sha256=("61c961fbdefec40ef2a383ff31208e8d1f6db3518e2ee97567c824751d88c74e"),
        semantic_claim=(
            "The model timing path selects positive custom delay or "
            "liveDelay, adding dynamic smoothing time. This is separate "
            "from the NN constructor and controlsd paths."
        ),
        conditions=("Model processing branch reaches the delay selection",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:delay-nn",
        parameter_ids=("SteerActuatorDelay",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.__init__",
        range_start=106,
        range_end=109,
        git_blob_sha="10c93b526fee645cba9dc1a6442ed118bf9eeff9",
        source_range_sha256=("69b8da38580c0adf799fe7bc3a08bb0db2dd8d320e239f5a02706331e00738fe"),
        semantic_claim=(
            "NN/NN-lite initialization caches stored delay times 0.01 plus "
            "0.3 seconds for desired lateral jerk timing; a raw zero is not "
            "a liveDelay substitution in this expression."
        ),
        conditions=("NN or NN-lite initialization branch",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:friction",
        parameter_ids=("LateralTorqueFriction",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="opendbc_repo/opendbc/car/__init__.py",
        symbol="get_friction",
        range_start=291,
        range_end=299,
        git_blob_sha="9202ab152e2e6f4e938e6870ca6db850dd33a309",
        source_range_sha256=("fff4a395d7d7ddaee0b1f614681823cba5e84f25c22807e2ce5bdadec24bfc3c"),
        semantic_claim=(
            "Friction compensation interpolates between negative and "
            "positive torque_params.friction around the acceleration-error "
            "deadzone; the value is disabled when friction_compensation is "
            "false."
        ),
        conditions=("Callback uses this helper", "Friction compensation flag is true"),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:key-defaults",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "SteerActuatorDelay",
            "SteerRatioRate",
        ),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/common/params_keys.h",
        symbol="Params key declarations",
        range_start=280,
        range_end=387,
        git_blob_sha="685671e76b7168a4e032d3f64efa7cf8749f6490",
        source_range_sha256=("d28d87187e0edcb26473e8e3331d228f1b31bdc4a75da9fb8164ea665e70bbcb"),
        semantic_claim=(
            "The eight steering keys are persistent integer-text settings. "
            "Native key defaults for custom mode and delay are zero while "
            "the catalog UI defaults differ. They are not baselines."
        ),
        conditions=("Descriptive registered source defaults only",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:linear",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="opendbc_repo/opendbc/car/interfaces.py",
        symbol="CarInterfaceBase.torque_from_lateral_accel_linear",
        range_start=593,
        range_end=597,
        git_blob_sha="7fb351a27a5821347cf0a7cc779b790b997d3a61",
        source_range_sha256=("30b1c1707d6360b6bc7970049ae1480d4276a37561293bdd89b190d04acdd88f"),
        semantic_claim=(
            "The default linear callback divides lateral acceleration by "
            "latAccelFactor and adds friction compensation. This does not "
            "establish equivalence for every brand or NN callback."
        ),
        conditions=("Default linear torque conversion callback is actually selected",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:live-tuple",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.update_live_torque_params",
        range_start=134,
        range_end=140,
        git_blob_sha="10c93b526fee645cba9dc1a6442ed118bf9eeff9",
        source_range_sha256=("fcc92cb040e249df3e63eebda4427e96bf162f1248b8e0cf25dd7e6b4fd2a3d9"),
        semantic_claim=(
            "When the cached custom mode is not positive, the supplied "
            "factor, offset and friction are assigned as a tuple. This "
            "setter has no owner revision or CAS contract."
        ),
        conditions=("Cached custom mode permits live setter", "Torque controller selected"),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:nn",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.__init__ / update",
        range_start=69,
        range_end=307,
        git_blob_sha="10c93b526fee645cba9dc1a6442ed118bf9eeff9",
        source_range_sha256=("421d9dbd2101ece4df1f8ce601334bbb7dd186797bd60842a382fe0e497ba6a7"),
        semantic_claim=(
            "Initialization captures the CP torque tuple as defaults. NN "
            "and NN-lite flags select alternative feedforward/error paths; "
            "controller gains and torque coefficients do not imply a "
            "universal physical torque response or identification result."
        ),
        conditions=("Actual brand callback and NN/NN-lite context must be known",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:offset-fit",
        parameter_ids=("liveTorqueParameters.latAccelOffset",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/locationd/torqued.py",
        symbol="TorqueEstimator.estimate_params",
        range_start=145,
        range_end=157,
        git_blob_sha="3a01d1b36b9d1b9ac23936cfb59e1a5373088809",
        source_range_sha256=("efa2cbfcc4a36b428c93f053afc47ed750c95f6c9a2fa40e02e0ddba5362ea09"),
        semantic_claim=(
            "The estimator produces an offset alongside slope and "
            "spread-based friction. This audit does not establish a "
            "universal canonical unit or qualified identification for that "
            "offset."
        ),
        conditions=("Valid estimator point bucket and source-specific calculation",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:offset-publish",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/locationd/torqued.py",
        symbol="TorqueEstimator.get_msg",
        range_start=207,
        range_end=242,
        git_blob_sha="3a01d1b36b9d1b9ac23936cfb59e1a5373088809",
        source_range_sha256=("bb16b3ce08d5384e53575e7a64d58f7d197be853f1c96cd9ec9de373dc23bf87"),
        semantic_claim=(
            "The filtered internal offset is copied to "
            "latAccelOffsetFiltered with factor/friction and "
            "version/useParams/validity evidence; no current value is read "
            "by the knowledge package."
        ),
        conditions=("Actual source message/validity is a separate future input",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:pid",
        parameter_ids=("LateralTorqueKf", "LateralTorqueKiV", "LateralTorqueKpV"),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/common/pid.py",
        symbol="PIDController.update",
        range_start=49,
        range_end=70,
        git_blob_sha="a75aa42731640260b0f20202541171ec3838360b",
        source_range_sha256=("d29d2e74de600292dbdf15fcdbc3e4eaa41e3e40c871447a62e0f95d89aa7f5a"),
        semantic_claim=(
            "The proportional term multiplies error by k_p, feedforward "
            "multiplies its input by k_f and the integral increment uses "
            "error times k_i times the controller time step. These are "
            "software coefficients, not vehicle-approved gains."
        ),
        conditions=(
            "The ordinary PIDController is used",
            "Torque controller error/feedforward domain remains mode-dependent",
        ),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:ratio",
        parameter_ids=("SteerRatioRate",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/controls/lib/steer_ratio.py",
        symbol="resolve_vehicle_model_steer_ratio",
        range_start=10,
        range_end=23,
        git_blob_sha="94f014fa4ad01c72796b8c673507776421819397",
        source_range_sha256=("d7cd8fbdbae9d517821109e09e54635403b4ee9516a56e6ebb2e0a12ca70b939"),
        semantic_claim=(
            "MEB returns the learned ratio directly before manual "
            "override/rate scaling; non-MEB applies a valid CustomSR "
            "override or learned ratio times stored rate times 0.01, with "
            "source fallback/floor."
        ),
        conditions=("Exact revision helper and CustomSR/platform conditions must be retained",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:settings-type",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "SteerActuatorDelay",
            "SteerRatioRate",
        ),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/carrot/server/services/params.py",
        symbol="put_typed",
        range_start=327,
        range_end=362,
        git_blob_sha="52448df1a020858e8ff7dda4fd2df7d191a92106",
        source_range_sha256=("9bf4cdd7c85b80b4768693b11fc462ecb2e8dde67628888f16023e0864f86c0e"),
        semantic_claim=(
            "Native integer keys use typed integer serialization; inferred "
            "catalog types are fallback behavior. UI values and stored "
            "defaults are descriptive, never trusted baselines."
        ),
        conditions=("Native Params type information or explicit fallback source",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:settings-write",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "SteerActuatorDelay",
            "SteerRatioRate",
        ),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/carrot/server/services/params.py",
        symbol="set_param_value",
        range_start=365,
        range_end=375,
        git_blob_sha="52448df1a020858e8ff7dda4fd2df7d191a92106",
        source_range_sha256=("7c141738aa219da6c17f197d8d111bd04389b110cfb36e683861b9664c4e47fc"),
        semantic_claim=(
            "The device settings service delegates typed writes to Params "
            "and has a metadata fallback for unregistered settings. This is "
            "a descriptive storage writer, not this package or an exclusive "
            "owner."
        ),
        conditions=("Reference source only; never invoked by knowledge",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:ui-LateralTorqueAccelFactor",
        parameter_ids=("LateralTorqueAccelFactor",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueAccelFactor]",
        range_start=670,
        range_end=685,
        git_blob_sha="67aa63ddf4ffef32a6cdef34f1bdcd017749e855",
        source_range_sha256=("01a4d209aa010c020038d561990b6e176ffbbecc000cbf7a954edd5542f4fdb7"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueAccelFactor is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:ui-LateralTorqueCustom",
        parameter_ids=("LateralTorqueCustom",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueCustom]",
        range_start=654,
        range_end=669,
        git_blob_sha="67aa63ddf4ffef32a6cdef34f1bdcd017749e855",
        source_range_sha256=("60f03b1f6c5da5719362657f333578018e81a1dd3028c089832a17ec30510063"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueCustom is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:ui-LateralTorqueFriction",
        parameter_ids=("LateralTorqueFriction",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueFriction]",
        range_start=686,
        range_end=701,
        git_blob_sha="67aa63ddf4ffef32a6cdef34f1bdcd017749e855",
        source_range_sha256=("206e214b9aa38c25f0081acb932f0819d8ca9b7222218f4ea2c891daa810bb52"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueFriction is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:ui-LateralTorqueKf",
        parameter_ids=("LateralTorqueKf",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueKf]",
        range_start=734,
        range_end=749,
        git_blob_sha="67aa63ddf4ffef32a6cdef34f1bdcd017749e855",
        source_range_sha256=("a3909a2a1c30f2865dea026e9e7180f416ab87c38a61f8d0509385c1905917fc"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueKf is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:ui-LateralTorqueKiV",
        parameter_ids=("LateralTorqueKiV",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueKiV]",
        range_start=718,
        range_end=733,
        git_blob_sha="67aa63ddf4ffef32a6cdef34f1bdcd017749e855",
        source_range_sha256=("db958a988af92decafea2b488ec9d0534a84ffec5ee861ef747b4b7749c8b211"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueKiV is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:ui-LateralTorqueKpV",
        parameter_ids=("LateralTorqueKpV",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueKpV]",
        range_start=702,
        range_end=717,
        git_blob_sha="67aa63ddf4ffef32a6cdef34f1bdcd017749e855",
        source_range_sha256=("de454805ef623e2a987957ba5f07fa8746112956f52cd4e35d680f7eb1e4d70f"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueKpV is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:ui-SteerActuatorDelay",
        parameter_ids=("SteerActuatorDelay",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[SteerActuatorDelay]",
        range_start=942,
        range_end=957,
        git_blob_sha="67aa63ddf4ffef32a6cdef34f1bdcd017749e855",
        source_range_sha256=("b2efc06e486a73cae32a1a77686413f3f37989142aa885c9bbe00d7d9448056c"),
        semantic_claim=(
            "Catalog UI range/default/label for SteerActuatorDelay is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:ui-SteerRatioRate",
        parameter_ids=("SteerRatioRate",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[SteerRatioRate]",
        range_start=1072,
        range_end=1088,
        git_blob_sha="67aa63ddf4ffef32a6cdef34f1bdcd017749e855",
        source_range_sha256=("b971ebc4baa4011248b280487a3f11011ca7cda65b117ebe6f9686a158290643"),
        semantic_claim=(
            "Catalog UI range/default/label for SteerRatioRate is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:vm",
        parameter_ids=("SteerRatioRate",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/selfdrive/controls/controlsd.py",
        symbol="Controls.state_control",
        range_start=112,
        range_end=116,
        git_blob_sha="d0adba6a80659424a907683d14d8292475ced76b",
        source_range_sha256=("c8e2f3dc3a7783df451b94b0ba95ce55dfdbfd39efed9594bc4b5e38f42241b4"),
        semantic_claim=(
            "The resolved ratio is passed to VehicleModel.update_params. "
            "Current upstream additionally updates live geometry; helper "
            "conversion equivalence does not prove equal VM output."
        ),
        conditions=("Source-specific vehicle model context is required",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="hoya:wire",
        parameter_ids=("liveTorqueParameters.latAccelOffset",),
        repository="ajouatom/openpilot",
        exact_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        path="openpilot/cereal/log.capnp",
        symbol="LiveTorqueParametersData",
        range_start=2334,
        range_end=2349,
        git_blob_sha="03f5b98cc953ee3382d2e9713e4f999548a9c9e1",
        source_range_sha256=("14671356ec6065f0ba48451a2bde026f7f788d6bd2bdf48c610673aa4b37d809"),
        semantic_claim=(
            "The schema names latAccelOffsetRaw and latAccelOffsetFiltered, "
            "not a literal latAccelOffset member. The catalog logical "
            "offset ID refers to the filtered consumed member; scalar "
            "default zero is not availability."
        ),
        conditions=("Legacy scalar defaults are never interpreted as available state",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
)

HOYA_PARAMETERS: tuple[ParameterDescriptor, ...] = (
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueAccelFactor",
        storage_key="LateralTorqueAccelFactor",
        display_name="LateralTorqueAccelFactor",
        domain="steering",
        family="torque_response",
        classification=Classification.TUNING_CANDIDATE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.001,
        canonical_unit=None,
        consumer_unit="default-linear m/s^2 per normalized torque",
        consumer_transform_description=(
            "Stored count times 0.001 in the positive custom torque branch."
        ),
        ui_unit_description="Catalog label denotes storage count times 0.001.",
        consumer_claim_ids=(
            "hoya:controlsd-live",
            "hoya:custom",
            "hoya:key-defaults",
            "hoya:linear",
            "hoya:live-tuple",
            "hoya:nn",
            "hoya:settings-type",
            "hoya:settings-write",
            "hoya:ui-LateralTorqueAccelFactor",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=2500,
        ui_catalog_min=1000,
        ui_catalog_max=6000,
        storage_registry_default=2500,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.torque_params.latAccelFactor",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        evidence_status=Confidence.CONDITIONAL,
        evidence_gaps=(
            "BRAND_NN_CALLBACK_SCOPE_UNRESOLVED",
            "OWNERSHIP_CONFLICT_UNRESOLVED",
            "UNRESOLVED_UNIT_EQUIVALENCE",
        ),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueCustom",
        storage_key="LateralTorqueCustom",
        display_name="LateralTorqueCustom",
        domain="steering",
        family="torque_mode",
        classification=Classification.MODE_SELECTOR,
        semantic_description=(
            "Selects a torque parameter ownership/consumer path, never a "
            "numerical application target."
        ),
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=1.0,
        canonical_unit="integer mode selector",
        consumer_unit="integer mode selector",
        consumer_transform_description=(
            "Positive sampled integer enables custom tuple/gain reads every "
            "ten frames; cached previous mode gates the live setter."
        ),
        ui_unit_description=("Integer selector; UI default 1 differs from native key default 0."),
        consumer_claim_ids=(
            "hoya:custom",
            "hoya:key-defaults",
            "hoya:live-tuple",
            "hoya:settings-type",
            "hoya:settings-write",
            "hoya:ui-LateralTorqueCustom",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=1,
        ui_catalog_min=0,
        ui_catalog_max=1,
        storage_registry_default=0,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_int; this package reads no values."
        ),
        runtime_field="LatControlTorque.lateralTorqueCustom",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED", "UI_NATIVE_DEFAULT_MISMATCH"),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueFriction",
        storage_key="LateralTorqueFriction",
        display_name="LateralTorqueFriction",
        domain="steering",
        family="torque_response",
        classification=Classification.TUNING_CANDIDATE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.001,
        canonical_unit=None,
        consumer_unit="default-linear normalized torque correction",
        consumer_transform_description=(
            "Stored count times 0.001 in the positive custom torque branch."
        ),
        ui_unit_description="Catalog label denotes storage count times 0.001.",
        consumer_claim_ids=(
            "hoya:controlsd-live",
            "hoya:custom",
            "hoya:friction",
            "hoya:key-defaults",
            "hoya:linear",
            "hoya:live-tuple",
            "hoya:nn",
            "hoya:settings-type",
            "hoya:settings-write",
            "hoya:ui-LateralTorqueFriction",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=100,
        ui_catalog_min=0,
        ui_catalog_max=1000,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.torque_params.friction",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        evidence_status=Confidence.CONDITIONAL,
        evidence_gaps=(
            "BRAND_NN_CALLBACK_SCOPE_UNRESOLVED",
            "OWNERSHIP_CONFLICT_UNRESOLVED",
            "UNRESOLVED_UNIT_EQUIVALENCE",
        ),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueKf",
        storage_key="LateralTorqueKf",
        display_name="LateralTorqueKf",
        domain="steering",
        family="torque_pid",
        classification=Classification.SAFETY_SENSITIVE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="PID feedforward software coefficient",
        consumer_unit="PID feedforward software coefficient",
        consumer_transform_description=(
            "Stored integer-text count times 0.01 assigns the torque PID "
            "feedforward coefficient; error/feedforward domain depends on "
            "the actual callback."
        ),
        ui_unit_description=(
            "English/Chinese UI titles denote times 0.001; Korean title and "
            "consumer denote times 0.01."
        ),
        consumer_claim_ids=(
            "hoya:custom",
            "hoya:key-defaults",
            "hoya:nn",
            "hoya:pid",
            "hoya:settings-type",
            "hoya:settings-write",
            "hoya:ui-LateralTorqueKf",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=100,
        ui_catalog_min=0,
        ui_catalog_max=200,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.pid.k_f",
        descriptive_owner=(
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED", "UI_LABEL_SCALE_MISMATCH"),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueKiV",
        storage_key="LateralTorqueKiV",
        display_name="LateralTorqueKiV",
        domain="steering",
        family="torque_pid",
        classification=Classification.SAFETY_SENSITIVE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="PID integral software coefficient",
        consumer_unit="PID integral software coefficient",
        consumer_transform_description=(
            "Stored integer-text count times 0.01 assigns the torque PID "
            "integral coefficient; error/feedforward domain depends on the "
            "actual callback."
        ),
        ui_unit_description="Catalog label denotes times 0.01.",
        consumer_claim_ids=(
            "hoya:custom",
            "hoya:key-defaults",
            "hoya:nn",
            "hoya:pid",
            "hoya:settings-type",
            "hoya:settings-write",
            "hoya:ui-LateralTorqueKiV",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=10,
        ui_catalog_min=0,
        ui_catalog_max=200,
        storage_registry_default=10,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.pid._k_i",
        descriptive_owner=(
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED",),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueKpV",
        storage_key="LateralTorqueKpV",
        display_name="LateralTorqueKpV",
        domain="steering",
        family="torque_pid",
        classification=Classification.SAFETY_SENSITIVE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="PID proportional software coefficient",
        consumer_unit="PID proportional software coefficient",
        consumer_transform_description=(
            "Stored integer-text count times 0.01 assigns the torque PID "
            "proportional coefficient; error/feedforward domain depends on "
            "the actual callback."
        ),
        ui_unit_description="Catalog label denotes times 0.01.",
        consumer_claim_ids=(
            "hoya:custom",
            "hoya:key-defaults",
            "hoya:nn",
            "hoya:pid",
            "hoya:settings-type",
            "hoya:settings-write",
            "hoya:ui-LateralTorqueKpV",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=100,
        ui_catalog_min=0,
        ui_catalog_max=200,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.pid._k_p",
        descriptive_owner=(
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED",),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="SteerActuatorDelay",
        storage_key="SteerActuatorDelay",
        display_name="SteerActuatorDelay",
        domain="steering",
        family="steering_delay",
        classification=Classification.DESCRIPTIVE_ONLY,
        semantic_description=(
            "Software delay selector used by several source-specific timing "
            "paths; not measured physical delay."
        ),
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="s",
        consumer_unit="s",
        consumer_transform_description=(
            "Stored count times 0.01 seconds. controlsd zero selects "
            "liveDelay; modeld selects positive custom or liveDelay plus "
            "smoothing; NN initialization separately caches raw scaled "
            "delay plus 0.3 seconds."
        ),
        ui_unit_description=(
            "Raw integer catalog value; title does not state the seconds multiplier."
        ),
        consumer_claim_ids=(
            "hoya:delay",
            "hoya:delay-model",
            "hoya:delay-nn",
            "hoya:key-defaults",
            "hoya:settings-type",
            "hoya:settings-write",
            "hoya:ui-SteerActuatorDelay",
        ),
        mode_conditions=(
            "Hoya controlsd reads on each state_control",
            "modeld positive custom selection is distinct from NN constructor timing",
        ),
        ui_default=30,
        ui_catalog_min=0,
        ui_catalog_max=300,
        storage_registry_default=0,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="controlsd / modeld / NN desired_lat_jerk_time",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=(
            "OWNERSHIP_CONFLICT_UNRESOLVED",
            "SOURCE_BRANCH_DRIFT",
            "UI_NATIVE_DEFAULT_MISMATCH",
        ),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="SteerRatioRate",
        storage_key="SteerRatioRate",
        display_name="SteerRatioRate",
        domain="steering",
        family="vehicle_model_ratio",
        classification=Classification.DESCRIPTIVE_ONLY,
        semantic_description=(
            "Scales or is bypassed/overridden in the source-specific VehicleModel ratio resolver."
        ),
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="dimensionless ratio multiplier",
        consumer_unit="dimensionless ratio multiplier",
        consumer_transform_description=(
            "MEB returns the learned ratio directly before manual "
            "override/rate scaling; non-MEB applies a valid CustomSR "
            "override or learned ratio times stored rate times 0.01, with "
            "source fallback/floor."
        ),
        ui_unit_description="Raw percent-like count; catalog label denotes times 0.01.",
        consumer_claim_ids=(
            "hoya:key-defaults",
            "hoya:ratio",
            "hoya:settings-type",
            "hoya:settings-write",
            "hoya:ui-SteerRatioRate",
            "hoya:vm",
        ),
        mode_conditions=("Hoya MEB bypass before custom/rate resolution",),
        ui_default=100,
        ui_catalog_min=30,
        ui_catalog_max=200,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="VehicleModel.update_params resolved steer ratio",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.UI_SETTINGS_WRITER,
            OwnerRole.VEHICLE_MODEL_CONSUMER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED", "SOURCE_BRANCH_DRIFT"),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="liveTorqueParameters.latAccelOffset",
        storage_key=None,
        display_name="liveTorqueParameters.latAccelOffset",
        domain="steering",
        family="torque_coupled_state",
        classification=Classification.COUPLED_PRESERVED_STATE,
        semantic_description=(
            "Logical preserved offset ID for the filtered wire state; not a "
            "literal wire field or tuning candidate."
        ),
        storage_type=StorageType.MESSAGE_FLOAT32,
        storage_unit="filtered message scalar",
        storage_scale=1.0,
        canonical_unit=None,
        consumer_unit=None,
        consumer_transform_description=(
            "latAccelOffsetFiltered is passed unchanged to the live tuple "
            "setter. Custom mode uses the captured CP offset. The default "
            "linear callback does not use the offset directly."
        ),
        ui_unit_description=None,
        consumer_claim_ids=(
            "hoya:controlsd-live",
            "hoya:linear",
            "hoya:live-tuple",
            "hoya:nn",
            "hoya:offset-fit",
            "hoya:offset-publish",
            "hoya:wire",
        ),
        mode_conditions=(
            "live validity/useParams and custom-mode conditions retained",
            "torque controller selected",
        ),
        ui_default=None,
        ui_catalog_min=None,
        ui_catalog_max=None,
        storage_registry_default=None,
        default_sources=(
            "No UI or available-state default; producer seed zero is not availability.",
        ),
        consumer_value_source=(
            "Future exact liveTorqueParameters message evidence only; no value read here."
        ),
        runtime_field="liveTorqueParameters.latAccelOffsetFiltered",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="0e9c589c1b83027146f909a9cdc306c2c665ceaf",
        evidence_status=Confidence.UNRESOLVED,
        evidence_gaps=(
            "LOGICAL_ID_NOT_WIRE_MEMBER",
            "OFFSET_CANONICAL_UNIT_UNRESOLVED",
            "OWNERSHIP_CONFLICT_UNRESOLVED",
        ),
    ),
)

RUNTIME_CLAIMS: tuple[SourceKnowledgeDescriptor, ...] = (
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:controlsd-live",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/controls/controlsd.py",
        symbol="Controls.state_control",
        range_start=138,
        range_end=142,
        git_blob_sha="2378902ba077177b96dfb57f010e06c388241213",
        source_range_sha256=("4243e06bf84c65290ff8e710ebd5997385a9c16cee62956df0769fa241f3c612"),
        semantic_claim=(
            "The liveTorqueParameters factorFiltered, offsetFiltered and "
            "frictionCoefficientFiltered are passed to the lateral torque "
            "setter after all_checks and useParams. No descriptive claim "
            "proves writer exclusivity."
        ),
        conditions=("SubMaster all_checks and useParams pass", "Torque lateral tuning selected"),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:custom",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.update",
        range_start=145,
        range_end=163,
        git_blob_sha="25cc7913dd62602dcc518b3d647069174919fe25",
        source_range_sha256=("55f7a8e7862b0ac88021ea905ff1e96b14e3fd2ad30aa81e039898b81da8c99a"),
        semantic_claim=(
            "A positive sampled custom mode assigns stored factor/friction "
            "times 0.001 and Kp/Ki/Kf times 0.01; it preserves the captured "
            "default offset. The prior cached mode also controls live "
            "updates."
        ),
        conditions=(
            "CP lateral tuning is torque",
            "Custom Params branch sampled every ten controller frames",
        ),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:delay",
        parameter_ids=("SteerActuatorDelay",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/controls/controlsd.py",
        symbol="Controls.state_control",
        range_start=200,
        range_end=205,
        git_blob_sha="2378902ba077177b96dfb57f010e06c388241213",
        source_range_sha256=("944f5276d05ad4f6cacb7524d2dcb54c9a5e7b9ea0304f98cc9d12bcc6c69ba5"),
        semantic_claim=(
            "The stored delay is converted by 0.01 seconds and a zero "
            "result selects liveDelay in this controlsd path. The path is "
            "unconditional here in historical Hoya but lane-plan/active "
            "conditional in runtime/current upstream."
        ),
        conditions=(
            "Keep source-specific control-flow guard",
            "Not a measured actuator delay or guaranteed response",
        ),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:delay-model",
        parameter_ids=("SteerActuatorDelay",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/modeld/modeld.py",
        symbol="modeld_thread",
        range_start=561,
        range_end=564,
        git_blob_sha="b800432ccc6ff7013fd0ed10131124518dfb2381",
        source_range_sha256=("61c961fbdefec40ef2a383ff31208e8d1f6db3518e2ee97567c824751d88c74e"),
        semantic_claim=(
            "The model timing path selects positive custom delay or "
            "liveDelay, adding dynamic smoothing time. This is separate "
            "from the NN constructor and controlsd paths."
        ),
        conditions=("Model processing branch reaches the delay selection",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:delay-nn",
        parameter_ids=("SteerActuatorDelay",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.__init__",
        range_start=107,
        range_end=110,
        git_blob_sha="25cc7913dd62602dcc518b3d647069174919fe25",
        source_range_sha256=("69b8da38580c0adf799fe7bc3a08bb0db2dd8d320e239f5a02706331e00738fe"),
        semantic_claim=(
            "NN/NN-lite initialization caches stored delay times 0.01 plus "
            "0.3 seconds for desired lateral jerk timing; a raw zero is not "
            "a liveDelay substitution in this expression."
        ),
        conditions=("NN or NN-lite initialization branch",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:friction",
        parameter_ids=("LateralTorqueFriction",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="opendbc_repo/opendbc/car/__init__.py",
        symbol="get_friction",
        range_start=291,
        range_end=299,
        git_blob_sha="9202ab152e2e6f4e938e6870ca6db850dd33a309",
        source_range_sha256=("fff4a395d7d7ddaee0b1f614681823cba5e84f25c22807e2ce5bdadec24bfc3c"),
        semantic_claim=(
            "Friction compensation interpolates between negative and "
            "positive torque_params.friction around the acceleration-error "
            "deadzone; the value is disabled when friction_compensation is "
            "false."
        ),
        conditions=("Callback uses this helper", "Friction compensation flag is true"),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:key-defaults",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "SteerActuatorDelay",
            "SteerRatioRate",
        ),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/common/params_keys.h",
        symbol="Params key declarations",
        range_start=292,
        range_end=416,
        git_blob_sha="0a5285bcf0d1f292919a20d07ae319497dc86be4",
        source_range_sha256=("e6ff0d9572c6516d7151310cea0e8048c57ac070c441afa30898f9fe25ba86fb"),
        semantic_claim=(
            "The eight steering keys are persistent integer-text settings. "
            "Native key defaults for custom mode and delay are zero while "
            "the catalog UI defaults differ. They are not baselines."
        ),
        conditions=("Descriptive registered source defaults only",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:linear",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="opendbc_repo/opendbc/car/interfaces.py",
        symbol="CarInterfaceBase.torque_from_lateral_accel_linear",
        range_start=411,
        range_end=415,
        git_blob_sha="43a3e9f952c7a7b9fb01dcc37aeb6a2291cc3ddf",
        source_range_sha256=("30b1c1707d6360b6bc7970049ae1480d4276a37561293bdd89b190d04acdd88f"),
        semantic_claim=(
            "The default linear callback divides lateral acceleration by "
            "latAccelFactor and adds friction compensation. This does not "
            "establish equivalence for every brand or NN callback."
        ),
        conditions=("Default linear torque conversion callback is actually selected",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:live-tuple",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.update_live_torque_params",
        range_start=135,
        range_end=141,
        git_blob_sha="25cc7913dd62602dcc518b3d647069174919fe25",
        source_range_sha256=("fcc92cb040e249df3e63eebda4427e96bf162f1248b8e0cf25dd7e6b4fd2a3d9"),
        semantic_claim=(
            "When the cached custom mode is not positive, the supplied "
            "factor, offset and friction are assigned as a tuple. This "
            "setter has no owner revision or CAS contract."
        ),
        conditions=("Cached custom mode permits live setter", "Torque controller selected"),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:nn",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.__init__ / update",
        range_start=70,
        range_end=310,
        git_blob_sha="25cc7913dd62602dcc518b3d647069174919fe25",
        source_range_sha256=("b83edec1ca8e087f517abf0535228b088ed63e615d5c711fe16ff6beaae4e410"),
        semantic_claim=(
            "Initialization captures the CP torque tuple as defaults. NN "
            "and NN-lite flags select alternative feedforward/error paths; "
            "controller gains and torque coefficients do not imply a "
            "universal physical torque response or identification result."
        ),
        conditions=("Actual brand callback and NN/NN-lite context must be known",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:offset-fit",
        parameter_ids=("liveTorqueParameters.latAccelOffset",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/locationd/torqued.py",
        symbol="TorqueEstimator.estimate_params",
        range_start=145,
        range_end=157,
        git_blob_sha="3a01d1b36b9d1b9ac23936cfb59e1a5373088809",
        source_range_sha256=("efa2cbfcc4a36b428c93f053afc47ed750c95f6c9a2fa40e02e0ddba5362ea09"),
        semantic_claim=(
            "The estimator produces an offset alongside slope and "
            "spread-based friction. This audit does not establish a "
            "universal canonical unit or qualified identification for that "
            "offset."
        ),
        conditions=("Valid estimator point bucket and source-specific calculation",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:offset-publish",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/locationd/torqued.py",
        symbol="TorqueEstimator.get_msg",
        range_start=207,
        range_end=242,
        git_blob_sha="3a01d1b36b9d1b9ac23936cfb59e1a5373088809",
        source_range_sha256=("bb16b3ce08d5384e53575e7a64d58f7d197be853f1c96cd9ec9de373dc23bf87"),
        semantic_claim=(
            "The filtered internal offset is copied to "
            "latAccelOffsetFiltered with factor/friction and "
            "version/useParams/validity evidence; no current value is read "
            "by the knowledge package."
        ),
        conditions=("Actual source message/validity is a separate future input",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:pid",
        parameter_ids=("LateralTorqueKf", "LateralTorqueKiV", "LateralTorqueKpV"),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/common/pid.py",
        symbol="PIDController.update",
        range_start=49,
        range_end=70,
        git_blob_sha="a75aa42731640260b0f20202541171ec3838360b",
        source_range_sha256=("d29d2e74de600292dbdf15fcdbc3e4eaa41e3e40c871447a62e0f95d89aa7f5a"),
        semantic_claim=(
            "The proportional term multiplies error by k_p, feedforward "
            "multiplies its input by k_f and the integral increment uses "
            "error times k_i times the controller time step. These are "
            "software coefficients, not vehicle-approved gains."
        ),
        conditions=(
            "The ordinary PIDController is used",
            "Torque controller error/feedforward domain remains mode-dependent",
        ),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:ratio",
        parameter_ids=("SteerRatioRate",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/controls/lib/steer_ratio.py",
        symbol="resolve_vehicle_model_steer_ratio",
        range_start=10,
        range_end=20,
        git_blob_sha="e679268b3e488a7eac11720a37f43d4a8fa2bb7a",
        source_range_sha256=("d4407c097aadf0e0345e838f0fe6ba1089afe59f5802185bca8b87045b51c6f2"),
        semantic_claim=(
            "All platforms use the helper manual CustomSR override or "
            "learned ratio times stored rate times 0.01, with source "
            "fallback/floor. There is no MEB bypass in this helper."
        ),
        conditions=("Exact revision helper and CustomSR/platform conditions must be retained",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:settings-type",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "SteerActuatorDelay",
            "SteerRatioRate",
        ),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/carrot/server/services/params.py",
        symbol="put_typed",
        range_start=335,
        range_end=370,
        git_blob_sha="c47770c7a9ac50dbcffda24714f8edcf3849e6a3",
        source_range_sha256=("9bf4cdd7c85b80b4768693b11fc462ecb2e8dde67628888f16023e0864f86c0e"),
        semantic_claim=(
            "Native integer keys use typed integer serialization; inferred "
            "catalog types are fallback behavior. UI values and stored "
            "defaults are descriptive, never trusted baselines."
        ),
        conditions=("Native Params type information or explicit fallback source",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:settings-write",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "SteerActuatorDelay",
            "SteerRatioRate",
        ),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/carrot/server/services/params.py",
        symbol="set_param_value",
        range_start=393,
        range_end=408,
        git_blob_sha="c47770c7a9ac50dbcffda24714f8edcf3849e6a3",
        source_range_sha256=("601aca703e8436abc3f27be340f550c0ce917d6f7c2d183d1e9b8dd11d36b674"),
        semantic_claim=(
            "The device settings service delegates typed writes to Params "
            "and has a metadata fallback for unregistered settings. This is "
            "a descriptive storage writer, not this package or an exclusive "
            "owner."
        ),
        conditions=("Reference source only; never invoked by knowledge",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:ui-LateralTorqueAccelFactor",
        parameter_ids=("LateralTorqueAccelFactor",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueAccelFactor]",
        range_start=715,
        range_end=730,
        git_blob_sha="b7e044a72f6acd254c82c88be8b4878f65237b93",
        source_range_sha256=("01a4d209aa010c020038d561990b6e176ffbbecc000cbf7a954edd5542f4fdb7"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueAccelFactor is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:ui-LateralTorqueCustom",
        parameter_ids=("LateralTorqueCustom",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueCustom]",
        range_start=699,
        range_end=714,
        git_blob_sha="b7e044a72f6acd254c82c88be8b4878f65237b93",
        source_range_sha256=("60f03b1f6c5da5719362657f333578018e81a1dd3028c089832a17ec30510063"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueCustom is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:ui-LateralTorqueFriction",
        parameter_ids=("LateralTorqueFriction",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueFriction]",
        range_start=731,
        range_end=746,
        git_blob_sha="b7e044a72f6acd254c82c88be8b4878f65237b93",
        source_range_sha256=("206e214b9aa38c25f0081acb932f0819d8ca9b7222218f4ea2c891daa810bb52"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueFriction is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:ui-LateralTorqueKf",
        parameter_ids=("LateralTorqueKf",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueKf]",
        range_start=779,
        range_end=794,
        git_blob_sha="b7e044a72f6acd254c82c88be8b4878f65237b93",
        source_range_sha256=("a3909a2a1c30f2865dea026e9e7180f416ab87c38a61f8d0509385c1905917fc"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueKf is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:ui-LateralTorqueKiV",
        parameter_ids=("LateralTorqueKiV",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueKiV]",
        range_start=763,
        range_end=778,
        git_blob_sha="b7e044a72f6acd254c82c88be8b4878f65237b93",
        source_range_sha256=("db958a988af92decafea2b488ec9d0534a84ffec5ee861ef747b4b7749c8b211"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueKiV is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:ui-LateralTorqueKpV",
        parameter_ids=("LateralTorqueKpV",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueKpV]",
        range_start=747,
        range_end=762,
        git_blob_sha="b7e044a72f6acd254c82c88be8b4878f65237b93",
        source_range_sha256=("de454805ef623e2a987957ba5f07fa8746112956f52cd4e35d680f7eb1e4d70f"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueKpV is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:ui-SteerActuatorDelay",
        parameter_ids=("SteerActuatorDelay",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[SteerActuatorDelay]",
        range_start=987,
        range_end=1002,
        git_blob_sha="b7e044a72f6acd254c82c88be8b4878f65237b93",
        source_range_sha256=("b2efc06e486a73cae32a1a77686413f3f37989142aa885c9bbe00d7d9448056c"),
        semantic_claim=(
            "Catalog UI range/default/label for SteerActuatorDelay is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:ui-SteerRatioRate",
        parameter_ids=("SteerRatioRate",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[SteerRatioRate]",
        range_start=1134,
        range_end=1150,
        git_blob_sha="b7e044a72f6acd254c82c88be8b4878f65237b93",
        source_range_sha256=("b971ebc4baa4011248b280487a3f11011ca7cda65b117ebe6f9686a158290643"),
        semantic_claim=(
            "Catalog UI range/default/label for SteerRatioRate is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:vm",
        parameter_ids=("SteerRatioRate",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/selfdrive/controls/controlsd.py",
        symbol="Controls.state_control",
        range_start=128,
        range_end=131,
        git_blob_sha="2378902ba077177b96dfb57f010e06c388241213",
        source_range_sha256=("2cd8c0320dbfc8aff61be9678749d731ab5ea8bc70a0179abd7e1155190c6c1a"),
        semantic_claim=(
            "The resolved ratio is passed to VehicleModel.update_params. "
            "Current upstream additionally updates live geometry; helper "
            "conversion equivalence does not prove equal VM output."
        ),
        conditions=("Source-specific vehicle model context is required",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="runtime:wire",
        parameter_ids=("liveTorqueParameters.latAccelOffset",),
        repository="rownlvh8875-coder/openpilot",
        exact_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        path="openpilot/cereal/log.capnp",
        symbol="LiveTorqueParametersData",
        range_start=2377,
        range_end=2392,
        git_blob_sha="9c5cebe0eaa6fbfa077e9e8bfd0b5161367ef862",
        source_range_sha256=("14671356ec6065f0ba48451a2bde026f7f788d6bd2bdf48c610673aa4b37d809"),
        semantic_claim=(
            "The schema names latAccelOffsetRaw and latAccelOffsetFiltered, "
            "not a literal latAccelOffset member. The catalog logical "
            "offset ID refers to the filtered consumed member; scalar "
            "default zero is not availability."
        ),
        conditions=("Legacy scalar defaults are never interpreted as available state",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
)

RUNTIME_PARAMETERS: tuple[ParameterDescriptor, ...] = (
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueAccelFactor",
        storage_key="LateralTorqueAccelFactor",
        display_name="LateralTorqueAccelFactor",
        domain="steering",
        family="torque_response",
        classification=Classification.TUNING_CANDIDATE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.001,
        canonical_unit=None,
        consumer_unit="default-linear m/s^2 per normalized torque",
        consumer_transform_description=(
            "Stored count times 0.001 in the positive custom torque branch."
        ),
        ui_unit_description="Catalog label denotes storage count times 0.001.",
        consumer_claim_ids=(
            "runtime:controlsd-live",
            "runtime:custom",
            "runtime:key-defaults",
            "runtime:linear",
            "runtime:live-tuple",
            "runtime:nn",
            "runtime:settings-type",
            "runtime:settings-write",
            "runtime:ui-LateralTorqueAccelFactor",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=2500,
        ui_catalog_min=1000,
        ui_catalog_max=6000,
        storage_registry_default=2500,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.torque_params.latAccelFactor",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        evidence_status=Confidence.CONDITIONAL,
        evidence_gaps=(
            "BRAND_NN_CALLBACK_SCOPE_UNRESOLVED",
            "OWNERSHIP_CONFLICT_UNRESOLVED",
            "UNRESOLVED_UNIT_EQUIVALENCE",
        ),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueCustom",
        storage_key="LateralTorqueCustom",
        display_name="LateralTorqueCustom",
        domain="steering",
        family="torque_mode",
        classification=Classification.MODE_SELECTOR,
        semantic_description=(
            "Selects a torque parameter ownership/consumer path, never a "
            "numerical application target."
        ),
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=1.0,
        canonical_unit="integer mode selector",
        consumer_unit="integer mode selector",
        consumer_transform_description=(
            "Positive sampled integer enables custom tuple/gain reads every "
            "ten frames; cached previous mode gates the live setter."
        ),
        ui_unit_description=("Integer selector; UI default 1 differs from native key default 0."),
        consumer_claim_ids=(
            "runtime:custom",
            "runtime:key-defaults",
            "runtime:live-tuple",
            "runtime:settings-type",
            "runtime:settings-write",
            "runtime:ui-LateralTorqueCustom",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=1,
        ui_catalog_min=0,
        ui_catalog_max=1,
        storage_registry_default=0,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_int; this package reads no values."
        ),
        runtime_field="LatControlTorque.lateralTorqueCustom",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED", "UI_NATIVE_DEFAULT_MISMATCH"),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueFriction",
        storage_key="LateralTorqueFriction",
        display_name="LateralTorqueFriction",
        domain="steering",
        family="torque_response",
        classification=Classification.TUNING_CANDIDATE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.001,
        canonical_unit=None,
        consumer_unit="default-linear normalized torque correction",
        consumer_transform_description=(
            "Stored count times 0.001 in the positive custom torque branch."
        ),
        ui_unit_description="Catalog label denotes storage count times 0.001.",
        consumer_claim_ids=(
            "runtime:controlsd-live",
            "runtime:custom",
            "runtime:friction",
            "runtime:key-defaults",
            "runtime:linear",
            "runtime:live-tuple",
            "runtime:nn",
            "runtime:settings-type",
            "runtime:settings-write",
            "runtime:ui-LateralTorqueFriction",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=100,
        ui_catalog_min=0,
        ui_catalog_max=1000,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.torque_params.friction",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        evidence_status=Confidence.CONDITIONAL,
        evidence_gaps=(
            "BRAND_NN_CALLBACK_SCOPE_UNRESOLVED",
            "OWNERSHIP_CONFLICT_UNRESOLVED",
            "UNRESOLVED_UNIT_EQUIVALENCE",
        ),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueKf",
        storage_key="LateralTorqueKf",
        display_name="LateralTorqueKf",
        domain="steering",
        family="torque_pid",
        classification=Classification.SAFETY_SENSITIVE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="PID feedforward software coefficient",
        consumer_unit="PID feedforward software coefficient",
        consumer_transform_description=(
            "Stored integer-text count times 0.01 assigns the torque PID "
            "feedforward coefficient; error/feedforward domain depends on "
            "the actual callback."
        ),
        ui_unit_description=(
            "English/Chinese UI titles denote times 0.001; Korean title and "
            "consumer denote times 0.01."
        ),
        consumer_claim_ids=(
            "runtime:custom",
            "runtime:key-defaults",
            "runtime:nn",
            "runtime:pid",
            "runtime:settings-type",
            "runtime:settings-write",
            "runtime:ui-LateralTorqueKf",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=100,
        ui_catalog_min=0,
        ui_catalog_max=200,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.pid.k_f",
        descriptive_owner=(
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED", "UI_LABEL_SCALE_MISMATCH"),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueKiV",
        storage_key="LateralTorqueKiV",
        display_name="LateralTorqueKiV",
        domain="steering",
        family="torque_pid",
        classification=Classification.SAFETY_SENSITIVE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="PID integral software coefficient",
        consumer_unit="PID integral software coefficient",
        consumer_transform_description=(
            "Stored integer-text count times 0.01 assigns the torque PID "
            "integral coefficient; error/feedforward domain depends on the "
            "actual callback."
        ),
        ui_unit_description="Catalog label denotes times 0.01.",
        consumer_claim_ids=(
            "runtime:custom",
            "runtime:key-defaults",
            "runtime:nn",
            "runtime:pid",
            "runtime:settings-type",
            "runtime:settings-write",
            "runtime:ui-LateralTorqueKiV",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=10,
        ui_catalog_min=0,
        ui_catalog_max=200,
        storage_registry_default=10,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.pid._k_i",
        descriptive_owner=(
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED",),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueKpV",
        storage_key="LateralTorqueKpV",
        display_name="LateralTorqueKpV",
        domain="steering",
        family="torque_pid",
        classification=Classification.SAFETY_SENSITIVE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="PID proportional software coefficient",
        consumer_unit="PID proportional software coefficient",
        consumer_transform_description=(
            "Stored integer-text count times 0.01 assigns the torque PID "
            "proportional coefficient; error/feedforward domain depends on "
            "the actual callback."
        ),
        ui_unit_description="Catalog label denotes times 0.01.",
        consumer_claim_ids=(
            "runtime:custom",
            "runtime:key-defaults",
            "runtime:nn",
            "runtime:pid",
            "runtime:settings-type",
            "runtime:settings-write",
            "runtime:ui-LateralTorqueKpV",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=100,
        ui_catalog_min=0,
        ui_catalog_max=200,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.pid._k_p",
        descriptive_owner=(
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED",),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="SteerActuatorDelay",
        storage_key="SteerActuatorDelay",
        display_name="SteerActuatorDelay",
        domain="steering",
        family="steering_delay",
        classification=Classification.DESCRIPTIVE_ONLY,
        semantic_description=(
            "Software delay selector used by several source-specific timing "
            "paths; not measured physical delay."
        ),
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="s",
        consumer_unit="s",
        consumer_transform_description=(
            "Stored count times 0.01 seconds. controlsd zero selects "
            "liveDelay; modeld selects positive custom or liveDelay plus "
            "smoothing; NN initialization separately caches raw scaled "
            "delay plus 0.3 seconds."
        ),
        ui_unit_description=(
            "Raw integer catalog value; title does not state the seconds multiplier."
        ),
        consumer_claim_ids=(
            "runtime:delay",
            "runtime:delay-model",
            "runtime:delay-nn",
            "runtime:key-defaults",
            "runtime:settings-type",
            "runtime:settings-write",
            "runtime:ui-SteerActuatorDelay",
        ),
        mode_conditions=(
            "Runtime/current controlsd reads in active lane-plan branch",
            "modeld positive custom selection is distinct from NN constructor timing",
        ),
        ui_default=30,
        ui_catalog_min=0,
        ui_catalog_max=300,
        storage_registry_default=0,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="controlsd / modeld / NN desired_lat_jerk_time",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=(
            "OWNERSHIP_CONFLICT_UNRESOLVED",
            "SOURCE_BRANCH_DRIFT",
            "UI_NATIVE_DEFAULT_MISMATCH",
        ),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="SteerRatioRate",
        storage_key="SteerRatioRate",
        display_name="SteerRatioRate",
        domain="steering",
        family="vehicle_model_ratio",
        classification=Classification.DESCRIPTIVE_ONLY,
        semantic_description=(
            "Scales or is bypassed/overridden in the source-specific VehicleModel ratio resolver."
        ),
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="dimensionless ratio multiplier",
        consumer_unit="dimensionless ratio multiplier",
        consumer_transform_description=(
            "All platforms use the helper manual CustomSR override or "
            "learned ratio times stored rate times 0.01, with source "
            "fallback/floor. There is no MEB bypass in this helper."
        ),
        ui_unit_description="Raw percent-like count; catalog label denotes times 0.01.",
        consumer_claim_ids=(
            "runtime:key-defaults",
            "runtime:ratio",
            "runtime:settings-type",
            "runtime:settings-write",
            "runtime:ui-SteerRatioRate",
            "runtime:vm",
        ),
        mode_conditions=("All platforms: CustomSR override precedes rate scaling",),
        ui_default=100,
        ui_catalog_min=30,
        ui_catalog_max=200,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="VehicleModel.update_params resolved steer ratio",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.UI_SETTINGS_WRITER,
            OwnerRole.VEHICLE_MODEL_CONSUMER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED", "SOURCE_BRANCH_DRIFT"),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="liveTorqueParameters.latAccelOffset",
        storage_key=None,
        display_name="liveTorqueParameters.latAccelOffset",
        domain="steering",
        family="torque_coupled_state",
        classification=Classification.COUPLED_PRESERVED_STATE,
        semantic_description=(
            "Logical preserved offset ID for the filtered wire state; not a "
            "literal wire field or tuning candidate."
        ),
        storage_type=StorageType.MESSAGE_FLOAT32,
        storage_unit="filtered message scalar",
        storage_scale=1.0,
        canonical_unit=None,
        consumer_unit=None,
        consumer_transform_description=(
            "latAccelOffsetFiltered is passed unchanged to the live tuple "
            "setter. Custom mode uses the captured CP offset. The default "
            "linear callback does not use the offset directly."
        ),
        ui_unit_description=None,
        consumer_claim_ids=(
            "runtime:controlsd-live",
            "runtime:linear",
            "runtime:live-tuple",
            "runtime:nn",
            "runtime:offset-fit",
            "runtime:offset-publish",
            "runtime:wire",
        ),
        mode_conditions=(
            "live validity/useParams and custom-mode conditions retained",
            "torque controller selected",
        ),
        ui_default=None,
        ui_catalog_min=None,
        ui_catalog_max=None,
        storage_registry_default=None,
        default_sources=(
            "No UI or available-state default; producer seed zero is not availability.",
        ),
        consumer_value_source=(
            "Future exact liveTorqueParameters message evidence only; no value read here."
        ),
        runtime_field="liveTorqueParameters.latAccelOffsetFiltered",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="c2130730239bcdb4cbde9361ab90c8d99aa4ff55",
        evidence_status=Confidence.UNRESOLVED,
        evidence_gaps=(
            "LOGICAL_ID_NOT_WIRE_MEMBER",
            "OFFSET_CANONICAL_UNIT_UNRESOLVED",
            "OWNERSHIP_CONFLICT_UNRESOLVED",
        ),
    ),
)

UPSTREAM_CLAIMS: tuple[SourceKnowledgeDescriptor, ...] = (
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:controlsd-live",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/controls/controlsd.py",
        symbol="Controls.state_control",
        range_start=135,
        range_end=139,
        git_blob_sha="7c52bf491a9fddd5faaa7c168414f1c00c322ff3",
        source_range_sha256=("4243e06bf84c65290ff8e710ebd5997385a9c16cee62956df0769fa241f3c612"),
        semantic_claim=(
            "The liveTorqueParameters factorFiltered, offsetFiltered and "
            "frictionCoefficientFiltered are passed to the lateral torque "
            "setter after all_checks and useParams. No descriptive claim "
            "proves writer exclusivity."
        ),
        conditions=("SubMaster all_checks and useParams pass", "Torque lateral tuning selected"),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:custom",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.update",
        range_start=144,
        range_end=162,
        git_blob_sha="10c93b526fee645cba9dc1a6442ed118bf9eeff9",
        source_range_sha256=("55f7a8e7862b0ac88021ea905ff1e96b14e3fd2ad30aa81e039898b81da8c99a"),
        semantic_claim=(
            "A positive sampled custom mode assigns stored factor/friction "
            "times 0.001 and Kp/Ki/Kf times 0.01; it preserves the captured "
            "default offset. The prior cached mode also controls live "
            "updates."
        ),
        conditions=(
            "CP lateral tuning is torque",
            "Custom Params branch sampled every ten controller frames",
        ),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:delay",
        parameter_ids=("SteerActuatorDelay",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/controls/controlsd.py",
        symbol="Controls.state_control",
        range_start=197,
        range_end=202,
        git_blob_sha="7c52bf491a9fddd5faaa7c168414f1c00c322ff3",
        source_range_sha256=("944f5276d05ad4f6cacb7524d2dcb54c9a5e7b9ea0304f98cc9d12bcc6c69ba5"),
        semantic_claim=(
            "The stored delay is converted by 0.01 seconds and a zero "
            "result selects liveDelay in this controlsd path. The path is "
            "unconditional here in historical Hoya but lane-plan/active "
            "conditional in runtime/current upstream."
        ),
        conditions=(
            "Keep source-specific control-flow guard",
            "Not a measured actuator delay or guaranteed response",
        ),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:delay-model",
        parameter_ids=("SteerActuatorDelay",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/modeld/modeld.py",
        symbol="modeld_thread",
        range_start=561,
        range_end=564,
        git_blob_sha="b800432ccc6ff7013fd0ed10131124518dfb2381",
        source_range_sha256=("61c961fbdefec40ef2a383ff31208e8d1f6db3518e2ee97567c824751d88c74e"),
        semantic_claim=(
            "The model timing path selects positive custom delay or "
            "liveDelay, adding dynamic smoothing time. This is separate "
            "from the NN constructor and controlsd paths."
        ),
        conditions=("Model processing branch reaches the delay selection",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:delay-nn",
        parameter_ids=("SteerActuatorDelay",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.__init__",
        range_start=106,
        range_end=109,
        git_blob_sha="10c93b526fee645cba9dc1a6442ed118bf9eeff9",
        source_range_sha256=("69b8da38580c0adf799fe7bc3a08bb0db2dd8d320e239f5a02706331e00738fe"),
        semantic_claim=(
            "NN/NN-lite initialization caches stored delay times 0.01 plus "
            "0.3 seconds for desired lateral jerk timing; a raw zero is not "
            "a liveDelay substitution in this expression."
        ),
        conditions=("NN or NN-lite initialization branch",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:friction",
        parameter_ids=("LateralTorqueFriction",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="opendbc_repo/opendbc/car/__init__.py",
        symbol="get_friction",
        range_start=291,
        range_end=299,
        git_blob_sha="9202ab152e2e6f4e938e6870ca6db850dd33a309",
        source_range_sha256=("fff4a395d7d7ddaee0b1f614681823cba5e84f25c22807e2ce5bdadec24bfc3c"),
        semantic_claim=(
            "Friction compensation interpolates between negative and "
            "positive torque_params.friction around the acceleration-error "
            "deadzone; the value is disabled when friction_compensation is "
            "false."
        ),
        conditions=("Callback uses this helper", "Friction compensation flag is true"),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:key-defaults",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "SteerActuatorDelay",
            "SteerRatioRate",
        ),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/common/params_keys.h",
        symbol="Params key declarations",
        range_start=293,
        range_end=419,
        git_blob_sha="5583afd70bfbd215869e3ee92412e8b750c9fde7",
        source_range_sha256=("d88202211ed7dc50b04770fe1dfb40cd0e6e2d8ae85d8d7d4c2b2252f511d295"),
        semantic_claim=(
            "The eight steering keys are persistent integer-text settings. "
            "Native key defaults for custom mode and delay are zero while "
            "the catalog UI defaults differ. They are not baselines."
        ),
        conditions=("Descriptive registered source defaults only",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:linear",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="opendbc_repo/opendbc/car/interfaces.py",
        symbol="CarInterfaceBase.torque_from_lateral_accel_linear",
        range_start=411,
        range_end=415,
        git_blob_sha="43a3e9f952c7a7b9fb01dcc37aeb6a2291cc3ddf",
        source_range_sha256=("30b1c1707d6360b6bc7970049ae1480d4276a37561293bdd89b190d04acdd88f"),
        semantic_claim=(
            "The default linear callback divides lateral acceleration by "
            "latAccelFactor and adds friction compensation. This does not "
            "establish equivalence for every brand or NN callback."
        ),
        conditions=("Default linear torque conversion callback is actually selected",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:live-tuple",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.update_live_torque_params",
        range_start=134,
        range_end=140,
        git_blob_sha="10c93b526fee645cba9dc1a6442ed118bf9eeff9",
        source_range_sha256=("fcc92cb040e249df3e63eebda4427e96bf162f1248b8e0cf25dd7e6b4fd2a3d9"),
        semantic_claim=(
            "When the cached custom mode is not positive, the supplied "
            "factor, offset and friction are assigned as a tuple. This "
            "setter has no owner revision or CAS contract."
        ),
        conditions=("Cached custom mode permits live setter", "Torque controller selected"),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:nn",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/controls/lib/latcontrol_torque.py",
        symbol="LatControlTorque.__init__ / update",
        range_start=69,
        range_end=307,
        git_blob_sha="10c93b526fee645cba9dc1a6442ed118bf9eeff9",
        source_range_sha256=("421d9dbd2101ece4df1f8ce601334bbb7dd186797bd60842a382fe0e497ba6a7"),
        semantic_claim=(
            "Initialization captures the CP torque tuple as defaults. NN "
            "and NN-lite flags select alternative feedforward/error paths; "
            "controller gains and torque coefficients do not imply a "
            "universal physical torque response or identification result."
        ),
        conditions=("Actual brand callback and NN/NN-lite context must be known",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:offset-fit",
        parameter_ids=("liveTorqueParameters.latAccelOffset",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/locationd/torqued.py",
        symbol="TorqueEstimator.estimate_params",
        range_start=145,
        range_end=157,
        git_blob_sha="3a01d1b36b9d1b9ac23936cfb59e1a5373088809",
        source_range_sha256=("efa2cbfcc4a36b428c93f053afc47ed750c95f6c9a2fa40e02e0ddba5362ea09"),
        semantic_claim=(
            "The estimator produces an offset alongside slope and "
            "spread-based friction. This audit does not establish a "
            "universal canonical unit or qualified identification for that "
            "offset."
        ),
        conditions=("Valid estimator point bucket and source-specific calculation",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:offset-publish",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueFriction",
            "liveTorqueParameters.latAccelOffset",
        ),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/locationd/torqued.py",
        symbol="TorqueEstimator.get_msg",
        range_start=207,
        range_end=242,
        git_blob_sha="3a01d1b36b9d1b9ac23936cfb59e1a5373088809",
        source_range_sha256=("bb16b3ce08d5384e53575e7a64d58f7d197be853f1c96cd9ec9de373dc23bf87"),
        semantic_claim=(
            "The filtered internal offset is copied to "
            "latAccelOffsetFiltered with factor/friction and "
            "version/useParams/validity evidence; no current value is read "
            "by the knowledge package."
        ),
        conditions=("Actual source message/validity is a separate future input",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:pid",
        parameter_ids=("LateralTorqueKf", "LateralTorqueKiV", "LateralTorqueKpV"),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/common/pid.py",
        symbol="PIDController.update",
        range_start=49,
        range_end=70,
        git_blob_sha="a75aa42731640260b0f20202541171ec3838360b",
        source_range_sha256=("d29d2e74de600292dbdf15fcdbc3e4eaa41e3e40c871447a62e0f95d89aa7f5a"),
        semantic_claim=(
            "The proportional term multiplies error by k_p, feedforward "
            "multiplies its input by k_f and the integral increment uses "
            "error times k_i times the controller time step. These are "
            "software coefficients, not vehicle-approved gains."
        ),
        conditions=(
            "The ordinary PIDController is used",
            "Torque controller error/feedforward domain remains mode-dependent",
        ),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:ratio",
        parameter_ids=("SteerRatioRate",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/controls/lib/steer_ratio.py",
        symbol="resolve_vehicle_model_steer_ratio",
        range_start=10,
        range_end=20,
        git_blob_sha="e679268b3e488a7eac11720a37f43d4a8fa2bb7a",
        source_range_sha256=("d4407c097aadf0e0345e838f0fe6ba1089afe59f5802185bca8b87045b51c6f2"),
        semantic_claim=(
            "All platforms use the helper manual CustomSR override or "
            "learned ratio times stored rate times 0.01, with source "
            "fallback/floor. There is no MEB bypass in this helper."
        ),
        conditions=("Exact revision helper and CustomSR/platform conditions must be retained",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:settings-type",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "SteerActuatorDelay",
            "SteerRatioRate",
        ),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/carrot/server/services/params.py",
        symbol="put_typed",
        range_start=338,
        range_end=373,
        git_blob_sha="f170137363da3357d2fead1f0442f5fe2af846d5",
        source_range_sha256=("9bf4cdd7c85b80b4768693b11fc462ecb2e8dde67628888f16023e0864f86c0e"),
        semantic_claim=(
            "Native integer keys use typed integer serialization; inferred "
            "catalog types are fallback behavior. UI values and stored "
            "defaults are descriptive, never trusted baselines."
        ),
        conditions=("Native Params type information or explicit fallback source",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:settings-write",
        parameter_ids=(
            "LateralTorqueAccelFactor",
            "LateralTorqueCustom",
            "LateralTorqueFriction",
            "LateralTorqueKf",
            "LateralTorqueKiV",
            "LateralTorqueKpV",
            "SteerActuatorDelay",
            "SteerRatioRate",
        ),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/carrot/server/services/params.py",
        symbol="set_param_value",
        range_start=396,
        range_end=411,
        git_blob_sha="f170137363da3357d2fead1f0442f5fe2af846d5",
        source_range_sha256=("601aca703e8436abc3f27be340f550c0ce917d6f7c2d183d1e9b8dd11d36b674"),
        semantic_claim=(
            "The device settings service delegates typed writes to Params "
            "and has a metadata fallback for unregistered settings. This is "
            "a descriptive storage writer, not this package or an exclusive "
            "owner."
        ),
        conditions=("Reference source only; never invoked by knowledge",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:ui-LateralTorqueAccelFactor",
        parameter_ids=("LateralTorqueAccelFactor",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueAccelFactor]",
        range_start=717,
        range_end=732,
        git_blob_sha="1d281b518bbaf321cce148fbcc0a6ca3432afc3c",
        source_range_sha256=("01a4d209aa010c020038d561990b6e176ffbbecc000cbf7a954edd5542f4fdb7"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueAccelFactor is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:ui-LateralTorqueCustom",
        parameter_ids=("LateralTorqueCustom",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueCustom]",
        range_start=701,
        range_end=716,
        git_blob_sha="1d281b518bbaf321cce148fbcc0a6ca3432afc3c",
        source_range_sha256=("60f03b1f6c5da5719362657f333578018e81a1dd3028c089832a17ec30510063"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueCustom is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:ui-LateralTorqueFriction",
        parameter_ids=("LateralTorqueFriction",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueFriction]",
        range_start=733,
        range_end=748,
        git_blob_sha="1d281b518bbaf321cce148fbcc0a6ca3432afc3c",
        source_range_sha256=("206e214b9aa38c25f0081acb932f0819d8ca9b7222218f4ea2c891daa810bb52"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueFriction is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:ui-LateralTorqueKf",
        parameter_ids=("LateralTorqueKf",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueKf]",
        range_start=781,
        range_end=796,
        git_blob_sha="1d281b518bbaf321cce148fbcc0a6ca3432afc3c",
        source_range_sha256=("a3909a2a1c30f2865dea026e9e7180f416ab87c38a61f8d0509385c1905917fc"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueKf is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:ui-LateralTorqueKiV",
        parameter_ids=("LateralTorqueKiV",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueKiV]",
        range_start=765,
        range_end=780,
        git_blob_sha="1d281b518bbaf321cce148fbcc0a6ca3432afc3c",
        source_range_sha256=("db958a988af92decafea2b488ec9d0534a84ffec5ee861ef747b4b7749c8b211"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueKiV is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:ui-LateralTorqueKpV",
        parameter_ids=("LateralTorqueKpV",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[LateralTorqueKpV]",
        range_start=749,
        range_end=764,
        git_blob_sha="1d281b518bbaf321cce148fbcc0a6ca3432afc3c",
        source_range_sha256=("de454805ef623e2a987957ba5f07fa8746112956f52cd4e35d680f7eb1e4d70f"),
        semantic_claim=(
            "Catalog UI range/default/label for LateralTorqueKpV is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:ui-SteerActuatorDelay",
        parameter_ids=("SteerActuatorDelay",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[SteerActuatorDelay]",
        range_start=989,
        range_end=1004,
        git_blob_sha="1d281b518bbaf321cce148fbcc0a6ca3432afc3c",
        source_range_sha256=("65a1b87ab757409d91b24e7278c7860f4819fe038f4acb59a21a528388326bcf"),
        semantic_claim=(
            "Catalog UI range/default/label for SteerActuatorDelay is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:ui-SteerRatioRate",
        parameter_ids=("SteerRatioRate",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/carrot_settings.json",
        symbol="params[SteerRatioRate]",
        range_start=1160,
        range_end=1176,
        git_blob_sha="1d281b518bbaf321cce148fbcc0a6ca3432afc3c",
        source_range_sha256=("b971ebc4baa4011248b280487a3f11011ca7cda65b117ebe6f9686a158290643"),
        semantic_claim=(
            "Catalog UI range/default/label for SteerRatioRate is "
            "descriptive; no application bounds or current value is "
            "established."
        ),
        conditions=("UI metadata only, not consumer unit proof",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:vm",
        parameter_ids=("SteerRatioRate",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/selfdrive/controls/controlsd.py",
        symbol="Controls.state_control",
        range_start=125,
        range_end=129,
        git_blob_sha="7c52bf491a9fddd5faaa7c168414f1c00c322ff3",
        source_range_sha256=("d08282329f6b28a73e7a156e112848cd1f1f97332445ff805e337b78cb5a0d46"),
        semantic_claim=(
            "The resolved ratio is passed to VehicleModel.update_params. "
            "Current upstream additionally updates live geometry; helper "
            "conversion equivalence does not prove equal VM output."
        ),
        conditions=("Source-specific vehicle model context is required",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
    SourceKnowledgeDescriptor(
        schema_version=1,
        claim_id="upstream:wire",
        parameter_ids=("liveTorqueParameters.latAccelOffset",),
        repository="ajouatom/openpilot",
        exact_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        path="openpilot/cereal/log.capnp",
        symbol="LiveTorqueParametersData",
        range_start=2375,
        range_end=2390,
        git_blob_sha="609cb5892185f11cb0ee6d2e91c081170d40d7e9",
        source_range_sha256=("14671356ec6065f0ba48451a2bde026f7f788d6bd2bdf48c610673aa4b37d809"),
        semantic_claim=(
            "The schema names latAccelOffsetRaw and latAccelOffsetFiltered, "
            "not a literal latAccelOffset member. The catalog logical "
            "offset ID refers to the filtered consumed member; scalar "
            "default zero is not availability."
        ),
        conditions=("Legacy scalar defaults are never interpreted as available state",),
        confidence=Confidence.PROVEN,
        schema_revision="steering-source-knowledge-v1",
        supersedes_claim_id=None,
    ),
)

UPSTREAM_PARAMETERS: tuple[ParameterDescriptor, ...] = (
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueAccelFactor",
        storage_key="LateralTorqueAccelFactor",
        display_name="LateralTorqueAccelFactor",
        domain="steering",
        family="torque_response",
        classification=Classification.TUNING_CANDIDATE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.001,
        canonical_unit=None,
        consumer_unit="default-linear m/s^2 per normalized torque",
        consumer_transform_description=(
            "Stored count times 0.001 in the positive custom torque branch."
        ),
        ui_unit_description="Catalog label denotes storage count times 0.001.",
        consumer_claim_ids=(
            "upstream:controlsd-live",
            "upstream:custom",
            "upstream:key-defaults",
            "upstream:linear",
            "upstream:live-tuple",
            "upstream:nn",
            "upstream:settings-type",
            "upstream:settings-write",
            "upstream:ui-LateralTorqueAccelFactor",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=2500,
        ui_catalog_min=1000,
        ui_catalog_max=6000,
        storage_registry_default=2500,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.torque_params.latAccelFactor",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        evidence_status=Confidence.CONDITIONAL,
        evidence_gaps=(
            "BRAND_NN_CALLBACK_SCOPE_UNRESOLVED",
            "OWNERSHIP_CONFLICT_UNRESOLVED",
            "UNRESOLVED_UNIT_EQUIVALENCE",
        ),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueCustom",
        storage_key="LateralTorqueCustom",
        display_name="LateralTorqueCustom",
        domain="steering",
        family="torque_mode",
        classification=Classification.MODE_SELECTOR,
        semantic_description=(
            "Selects a torque parameter ownership/consumer path, never a "
            "numerical application target."
        ),
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=1.0,
        canonical_unit="integer mode selector",
        consumer_unit="integer mode selector",
        consumer_transform_description=(
            "Positive sampled integer enables custom tuple/gain reads every "
            "ten frames; cached previous mode gates the live setter."
        ),
        ui_unit_description=("Integer selector; UI default 1 differs from native key default 0."),
        consumer_claim_ids=(
            "upstream:custom",
            "upstream:key-defaults",
            "upstream:live-tuple",
            "upstream:settings-type",
            "upstream:settings-write",
            "upstream:ui-LateralTorqueCustom",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=1,
        ui_catalog_min=0,
        ui_catalog_max=1,
        storage_registry_default=0,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_int; this package reads no values."
        ),
        runtime_field="LatControlTorque.lateralTorqueCustom",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED", "UI_NATIVE_DEFAULT_MISMATCH"),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueFriction",
        storage_key="LateralTorqueFriction",
        display_name="LateralTorqueFriction",
        domain="steering",
        family="torque_response",
        classification=Classification.TUNING_CANDIDATE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.001,
        canonical_unit=None,
        consumer_unit="default-linear normalized torque correction",
        consumer_transform_description=(
            "Stored count times 0.001 in the positive custom torque branch."
        ),
        ui_unit_description="Catalog label denotes storage count times 0.001.",
        consumer_claim_ids=(
            "upstream:controlsd-live",
            "upstream:custom",
            "upstream:friction",
            "upstream:key-defaults",
            "upstream:linear",
            "upstream:live-tuple",
            "upstream:nn",
            "upstream:settings-type",
            "upstream:settings-write",
            "upstream:ui-LateralTorqueFriction",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=100,
        ui_catalog_min=0,
        ui_catalog_max=1000,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.torque_params.friction",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        evidence_status=Confidence.CONDITIONAL,
        evidence_gaps=(
            "BRAND_NN_CALLBACK_SCOPE_UNRESOLVED",
            "OWNERSHIP_CONFLICT_UNRESOLVED",
            "UNRESOLVED_UNIT_EQUIVALENCE",
        ),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueKf",
        storage_key="LateralTorqueKf",
        display_name="LateralTorqueKf",
        domain="steering",
        family="torque_pid",
        classification=Classification.SAFETY_SENSITIVE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="PID feedforward software coefficient",
        consumer_unit="PID feedforward software coefficient",
        consumer_transform_description=(
            "Stored integer-text count times 0.01 assigns the torque PID "
            "feedforward coefficient; error/feedforward domain depends on "
            "the actual callback."
        ),
        ui_unit_description=(
            "English/Chinese UI titles denote times 0.001; Korean title and "
            "consumer denote times 0.01."
        ),
        consumer_claim_ids=(
            "upstream:custom",
            "upstream:key-defaults",
            "upstream:nn",
            "upstream:pid",
            "upstream:settings-type",
            "upstream:settings-write",
            "upstream:ui-LateralTorqueKf",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=100,
        ui_catalog_min=0,
        ui_catalog_max=200,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.pid.k_f",
        descriptive_owner=(
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED", "UI_LABEL_SCALE_MISMATCH"),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueKiV",
        storage_key="LateralTorqueKiV",
        display_name="LateralTorqueKiV",
        domain="steering",
        family="torque_pid",
        classification=Classification.SAFETY_SENSITIVE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="PID integral software coefficient",
        consumer_unit="PID integral software coefficient",
        consumer_transform_description=(
            "Stored integer-text count times 0.01 assigns the torque PID "
            "integral coefficient; error/feedforward domain depends on the "
            "actual callback."
        ),
        ui_unit_description="Catalog label denotes times 0.01.",
        consumer_claim_ids=(
            "upstream:custom",
            "upstream:key-defaults",
            "upstream:nn",
            "upstream:pid",
            "upstream:settings-type",
            "upstream:settings-write",
            "upstream:ui-LateralTorqueKiV",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=10,
        ui_catalog_min=0,
        ui_catalog_max=200,
        storage_registry_default=10,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.pid._k_i",
        descriptive_owner=(
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED",),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="LateralTorqueKpV",
        storage_key="LateralTorqueKpV",
        display_name="LateralTorqueKpV",
        domain="steering",
        family="torque_pid",
        classification=Classification.SAFETY_SENSITIVE,
        semantic_description="Source-bound steering coefficient description only.",
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="PID proportional software coefficient",
        consumer_unit="PID proportional software coefficient",
        consumer_transform_description=(
            "Stored integer-text count times 0.01 assigns the torque PID "
            "proportional coefficient; error/feedforward domain depends on "
            "the actual callback."
        ),
        ui_unit_description="Catalog label denotes times 0.01.",
        consumer_claim_ids=(
            "upstream:custom",
            "upstream:key-defaults",
            "upstream:nn",
            "upstream:pid",
            "upstream:settings-type",
            "upstream:settings-write",
            "upstream:ui-LateralTorqueKpV",
        ),
        mode_conditions=(
            "custom versus live and NN/brand callback must be retained",
            "torque controller selected",
        ),
        ui_default=100,
        ui_catalog_min=0,
        ui_catalog_max=200,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="LatControlTorque.pid._k_p",
        descriptive_owner=(
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED",),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="SteerActuatorDelay",
        storage_key="SteerActuatorDelay",
        display_name="SteerActuatorDelay",
        domain="steering",
        family="steering_delay",
        classification=Classification.DESCRIPTIVE_ONLY,
        semantic_description=(
            "Software delay selector used by several source-specific timing "
            "paths; not measured physical delay."
        ),
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="s",
        consumer_unit="s",
        consumer_transform_description=(
            "Stored count times 0.01 seconds. controlsd zero selects "
            "liveDelay; modeld selects positive custom or liveDelay plus "
            "smoothing; NN initialization separately caches raw scaled "
            "delay plus 0.3 seconds."
        ),
        ui_unit_description=(
            "Raw integer catalog value; title does not state the seconds multiplier."
        ),
        consumer_claim_ids=(
            "upstream:delay",
            "upstream:delay-model",
            "upstream:delay-nn",
            "upstream:key-defaults",
            "upstream:settings-type",
            "upstream:settings-write",
            "upstream:ui-SteerActuatorDelay",
        ),
        mode_conditions=(
            "Runtime/current controlsd reads in active lane-plan branch",
            "modeld positive custom selection is distinct from NN constructor timing",
        ),
        ui_default=30,
        ui_catalog_min=0,
        ui_catalog_max=300,
        storage_registry_default=0,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="controlsd / modeld / NN desired_lat_jerk_time",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=(
            "OWNERSHIP_CONFLICT_UNRESOLVED",
            "SOURCE_BRANCH_DRIFT",
            "UI_NATIVE_DEFAULT_MISMATCH",
        ),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="SteerRatioRate",
        storage_key="SteerRatioRate",
        display_name="SteerRatioRate",
        domain="steering",
        family="vehicle_model_ratio",
        classification=Classification.DESCRIPTIVE_ONLY,
        semantic_description=(
            "Scales or is bypassed/overridden in the source-specific VehicleModel ratio resolver."
        ),
        storage_type=StorageType.INTEGER_TEXT,
        storage_unit="raw integer setting count",
        storage_scale=0.01,
        canonical_unit="dimensionless ratio multiplier",
        consumer_unit="dimensionless ratio multiplier",
        consumer_transform_description=(
            "All platforms use the helper manual CustomSR override or "
            "learned ratio times stored rate times 0.01, with source "
            "fallback/floor. There is no MEB bypass in this helper."
        ),
        ui_unit_description="Raw percent-like count; catalog label denotes times 0.01.",
        consumer_claim_ids=(
            "upstream:key-defaults",
            "upstream:ratio",
            "upstream:settings-type",
            "upstream:settings-write",
            "upstream:ui-SteerRatioRate",
            "upstream:vm",
        ),
        mode_conditions=("All platforms: CustomSR override precedes rate scaling",),
        ui_default=100,
        ui_catalog_min=30,
        ui_catalog_max=200,
        storage_registry_default=100,
        default_sources=("pinned UI catalog and native key registry; neither is a baseline",),
        consumer_value_source=(
            "Reference consumer reads Params.get_float; this package reads no values."
        ),
        runtime_field="VehicleModel.update_params resolved steer ratio",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.UI_SETTINGS_WRITER,
            OwnerRole.VEHICLE_MODEL_CONSUMER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        evidence_status=Confidence.PROVEN,
        evidence_gaps=("OWNERSHIP_CONFLICT_UNRESOLVED", "SOURCE_BRANCH_DRIFT"),
    ),
    ParameterDescriptor(
        schema_version=1,
        parameter_id="liveTorqueParameters.latAccelOffset",
        storage_key=None,
        display_name="liveTorqueParameters.latAccelOffset",
        domain="steering",
        family="torque_coupled_state",
        classification=Classification.COUPLED_PRESERVED_STATE,
        semantic_description=(
            "Logical preserved offset ID for the filtered wire state; not a "
            "literal wire field or tuning candidate."
        ),
        storage_type=StorageType.MESSAGE_FLOAT32,
        storage_unit="filtered message scalar",
        storage_scale=1.0,
        canonical_unit=None,
        consumer_unit=None,
        consumer_transform_description=(
            "latAccelOffsetFiltered is passed unchanged to the live tuple "
            "setter. Custom mode uses the captured CP offset. The default "
            "linear callback does not use the offset directly."
        ),
        ui_unit_description=None,
        consumer_claim_ids=(
            "upstream:controlsd-live",
            "upstream:linear",
            "upstream:live-tuple",
            "upstream:nn",
            "upstream:offset-fit",
            "upstream:offset-publish",
            "upstream:wire",
        ),
        mode_conditions=(
            "live validity/useParams and custom-mode conditions retained",
            "torque controller selected",
        ),
        ui_default=None,
        ui_catalog_min=None,
        ui_catalog_max=None,
        storage_registry_default=None,
        default_sources=(
            "No UI or available-state default; producer seed zero is not availability.",
        ),
        consumer_value_source=(
            "Future exact liveTorqueParameters message evidence only; no value read here."
        ),
        runtime_field="liveTorqueParameters.latAccelOffsetFiltered",
        descriptive_owner=(
            OwnerRole.CONTROLSD_CONSUMER,
            OwnerRole.CUSTOM_TORQUE_OVERRIDE,
            OwnerRole.NN_ALTERNATIVE,
            OwnerRole.TORQUED_PRODUCER,
            OwnerRole.UI_SETTINGS_WRITER,
        ),
        ownership_status=OwnershipStatus.CONFLICT_UNRESOLVED,
        source_revision="f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3",
        evidence_status=Confidence.UNRESOLVED,
        evidence_gaps=(
            "LOGICAL_ID_NOT_WIRE_MEMBER",
            "OFFSET_CANONICAL_UNIT_UNRESOLVED",
            "OWNERSHIP_CONFLICT_UNRESOLVED",
        ),
    ),
)

CATALOGS: tuple[KnowledgeRegistry, ...] = (
    KnowledgeRegistry("0e9c589c1b83027146f909a9cdc306c2c665ceaf", HOYA_PARAMETERS, HOYA_CLAIMS),
    KnowledgeRegistry(
        "c2130730239bcdb4cbde9361ab90c8d99aa4ff55", RUNTIME_PARAMETERS, RUNTIME_CLAIMS
    ),
    KnowledgeRegistry(
        "f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3", UPSTREAM_PARAMETERS, UPSTREAM_CLAIMS
    ),
)
