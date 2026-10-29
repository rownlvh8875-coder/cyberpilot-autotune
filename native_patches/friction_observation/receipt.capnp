@0xb526ba661d550a59;

# Exact-R passive receipt payload. Not deployed; no authority fields.

struct OptionalBool {
  union {
    unavailable @0 :Void;
    value @1 :Bool;
  }
}

struct OptionalDigest {
  union {
    unavailable @0 :Void;
    value @1 :Data;
  }
}

struct OptionalFloat64 {
  union {
    unavailable @0 :Void;
    value @1 :Float64;
  }
}

struct OptionalUInt64 {
  union {
    unavailable @0 :Void;
    value @1 :UInt64;
  }
}

enum AlignmentMethod {
  unknown @0;
  rawCallbackNoAlignment @1;
  singleDownstreamPair @2;
  coreValuesShifted @3;
}

enum CallbackFamily {
  unknown @0;
  linear @1;
  nnLite @2;
  nn @3;
  gmSiglin @4;
  gmNeural @5;
  other @6;
}

enum CallbackFunction {
  unknown @0;
  carInterfaceBaseTorqueFromLateralAccelLinear @1;
  carInterfaceTorqueFromLateralAccelSiglin @2;
  carInterfaceTorqueFromLateralAccelNeural @3;
  getFfNn @4;
  other @5;
}

enum CallbackSite {
  unknown @0;
  feedforward @1;
  setpoint @2;
  measurement @3;
  nnFrictionOverride @4;
}

enum CallbackStage {
  unknown @0;
  linearCallbackPrePid @1;
  nnLiteCallbackPrePid @2;
  nnCallbackPrePid @3;
  gmSiglinCallbackPrePid @4;
  otherUnsupported @5;
}

enum ClockDomain {
  unknown @0;
  monotonic @1;
  sensor @2;
}

enum ControllerMode {
  unknown @0;
  standard @1;
  custom @2;
}

enum DelaySource {
  unknown @0;
  staticCp @1;
  manual @2;
  liveDelay @3;
  unavailable @4;
}

enum GeometryOrigin {
  unknown @0;
  staticCpBaselineAppliedVm @1;
  actuallyAppliedVm @2;
  requestedNotApplied @3;
  liveParametersCandidate @4;
  unavailable @5;
}

enum OffsetSource {
  unknown @0;
  installedButUnusedLinear @1;
  filteredLiveContextOnly @2;
  rawLiveContextOnly @3;
  unavailable @4;
}

enum Precision {
  unknown @0;
  controllerLocalBinary64 @1;
  legacyFloat32 @2;
}

enum ScalarOrigin {
  unknown @0;
  localDirect @1;
  helperObserved @2;
  legacyPublished @3;
  reconstructedDiagnostic @4;
  derivedFromInstalledC @5;
  downstream @6;
  unavailable @7;
}

enum Signal {
  unknown @0;
  desiredLateralAccel @1;
  actualLateralAccel @2;
  roll @3;
  rollCompensation @4;
  callbackAcceleration @5;
  frictionInput @6;
  frictionDeadzone @7;
  frictionThreshold @8;
  qObserved @9;
  callbackOutputRaw @10;
  pidP @11;
  pidI @12;
  pidD @13;
  pidF @14;
  pidSum @15;
  postPidOutput @16;
  requestedTorque @17;
  hostOutput @18;
  appliedTorque @19;
}

enum SourceOrigin {
  unknown @0;
  wireEvent @1;
  localCycleObject @2;
}

enum SourceRole {
  unknown @0;
  carState @1;
  livePose @2;
  liveParameters @3;
  carControl @4;
  modelV2 @5;
  controlState @6;
  liveDelay @7;
}

enum Stage {
  unknown @0;
  callbackInput @1;
  helperQ @2;
  rawCallbackPrePidKf @3;
  pidP @4;
  pidI @5;
  pidD @6;
  pidScaledF @7;
  pidPreClipSum @8;
  pidPostClipInternalSign @9;
  requestedActuatorTorque @10;
  hostControllerOutput @11;
  appliedNormalizedTorque @12;
}

struct CycleIdentity {
  sessionId @0 :OptionalDigest;
  controllerCycleId @1 :OptionalUInt64;
  controllerCycleStartMonoTimeNs @2 :OptionalUInt64;
  contextCaptureMonoTimeNs @3 :OptionalUInt64;
  callbackEnterMonoTimeNs @4 :OptionalUInt64;
  callbackExitMonoTimeNs @5 :OptionalUInt64;
  controlEventMonoTimeNs @6 :OptionalUInt64;
  receiptCompleteMonoTimeNs @7 :OptionalUInt64;
  sourceRevision @8 :OptionalDigest;
  sourceSchemaDigest @9 :OptionalDigest;
  vehicleContextDigest @10 :OptionalDigest;
  controllerInstanceGeneration @11 :OptionalUInt64;
  installedParameterGeneration @12 :OptionalUInt64;
  geometryGeneration @13 :OptionalUInt64;
  callbackInvocationIndex @14 :OptionalUInt64;
  clockDomain @15 :ClockDomain;
}

struct ConsumedSourceIdentity {
  role @0 :SourceRole;
  sourceTimeNs @1 :OptionalUInt64;
  clockDomain @2 :ClockDomain;
  sequence @3 :OptionalUInt64;
  sourceIdentity @4 :OptionalDigest;
  consumed @5 :OptionalBool;
  valid @6 :OptionalBool;
  alive @7 :OptionalBool;
  origin @8 :SourceOrigin;
  controllerCycleDigest @9 :OptionalDigest;
}

struct ScalarObservation {
  signal @0 :Signal;
  stage @1 :Stage;
  value @2 :OptionalFloat64;
  precision @3 :Precision;
  origin @4 :ScalarOrigin;
  cycleDigest @5 :OptionalDigest;
  capturedMonoTimeNs @6 :OptionalUInt64;
}

struct ControllerCallbackSignals {
  desiredLateralAccel @0 :ScalarObservation;
  actualLateralAccel @1 :ScalarObservation;
  roll @2 :ScalarObservation;
  rollCompensation @3 :ScalarObservation;
  callbackAcceleration @4 :ScalarObservation;
  frictionInput @5 :ScalarObservation;
  frictionDeadzone @6 :ScalarObservation;
  frictionThreshold @7 :ScalarObservation;
  qObserved @8 :ScalarObservation;
  frictionCompensationEnabled @9 :OptionalBool;
  gravityAdjusted @10 :OptionalBool;
}

struct ControllerStageDecomposition {
  callbackOutputRaw @0 :ScalarObservation;
  pidP @1 :ScalarObservation;
  pidI @2 :ScalarObservation;
  pidD @3 :ScalarObservation;
  pidF @4 :ScalarObservation;
  pidSum @5 :ScalarObservation;
  postPidOutput @6 :ScalarObservation;
  requestedTorque @7 :ScalarObservation;
  hostOutput @8 :ScalarObservation;
  appliedTorque @9 :ScalarObservation;
  downstreamCycleId @10 :OptionalDigest;
  downstreamIdentities @11 :List(DownstreamStageIdentity);
}

struct DownstreamStageIdentity {
  stage @0 :Stage;
  sourceEventId @1 :OptionalDigest;
  sourceCommandEventId @2 :OptionalDigest;
  sourceTimeNs @3 :OptionalUInt64;
  clockDomain @4 :ClockDomain;
  controllerCycleDigest @5 :OptionalDigest;
  exactSourceCommandReference @6 :OptionalBool;
  sourceValid @7 :OptionalBool;
  sourceTransportHealthy @8 :OptionalBool;
}

struct LimitState {
  controllerActive @0 :OptionalBool;
  sourceHealthy @1 :OptionalBool;
  steeringPressed @2 :OptionalBool;
  driverOverride @3 :OptionalBool;
  timerSaturated @4 :OptionalBool;
  instantaneousControllerLimited @5 :OptionalBool;
  curvatureLimited @6 :OptionalBool;
  steerLimitedByControls @7 :OptionalBool;
  vehicleActuatorLimited @8 :OptionalBool;
}

struct InstalledParameters {
  generation @0 :OptionalUInt64;
  factorInstalled @1 :OptionalFloat64;
  frictionInstalled @2 :OptionalFloat64;
  offsetInstalled @3 :OptionalFloat64;
  offsetSource @4 :OffsetSource;
  sourceField @5 :Text;
  precision @6 :Precision;
  customSelector @7 :OptionalUInt64;
}

struct GainSnapshot {
  generation @0 :OptionalUInt64;
  kP @1 :OptionalFloat64;
  kI @2 :OptionalFloat64;
  kD @3 :OptionalFloat64;
  kF @4 :OptionalFloat64;
  precision @5 :Precision;
  cycleDigest @6 :OptionalDigest;
  capturedMonoTimeNs @7 :OptionalUInt64;
}

struct AppliedGeometryContext {
  sourceRevision @0 :OptionalDigest;
  vehicleContextDigest @1 :OptionalDigest;
  generation @2 :OptionalUInt64;
  appliedVmContextId @3 :OptionalDigest;
  origin @4 :GeometryOrigin;
  wheelbase @5 :OptionalFloat64;
  centerToFront @6 :OptionalFloat64;
  centerToFrontRatio @7 :OptionalFloat64;
  stiffnessFactor @8 :OptionalFloat64;
  effectiveSteerRatio @9 :OptionalFloat64;
  steerRatioRateRaw @10 :OptionalFloat64;
  steerRatioRateEffective @11 :OptionalFloat64;
  customSrRaw @12 :OptionalFloat64;
  customSrEffective @13 :OptionalFloat64;
  precision @14 :Precision;
  requestedCenterToFrontPercent @15 :OptionalUInt64;
  paramsdTargetRatio @16 :OptionalFloat64;
  liveParametersRatio @17 :OptionalFloat64;
}

struct DelayContext {
  effectiveDelayS @0 :OptionalFloat64;
  source @1 :DelaySource;
  alignmentMethod @2 :AlignmentMethod;
  alignmentVersion @3 :Text;
  correctionCount @4 :OptionalUInt64;
  samplePairId @5 :OptionalDigest;
  valuesAlreadyAligned @6 :OptionalBool;
}

struct FrictionObservationContext {
  cycleDigest @0 :OptionalDigest;
  snapshotTimeNs @1 :OptionalUInt64;
  installed @2 :InstalledParameters;
  gains @3 :GainSnapshot;
  geometry @4 :AppliedGeometryContext;
  delay @5 :DelayContext;
}

struct LateralTorqueIdentificationReceipt @0xda96579883444c35 {
  cycle @0 :CycleIdentity;
  callbackStage @1 :CallbackStage;
  controllerMode @2 :ControllerMode;
  callbackFamily @3 :CallbackFamily;
  callbackFunction @4 :CallbackFunction;
  callbackSite @5 :CallbackSite;
  sources @6 :List(ConsumedSourceIdentity);
  signals @7 :ControllerCallbackSignals;
  stages @8 :ControllerStageDecomposition;
  context @9 :FrictionObservationContext;
  limits @10 :LimitState;
  receiptSchemaVersion @11 :Text;
  consumptionManifestComplete @12 :OptionalBool;
}
