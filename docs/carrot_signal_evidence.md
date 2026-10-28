# Phase 8A synthetic signal evidence

Status: **CONTRACT_BLOCKED_REQUIRED_SIGNAL_UNRESOLVED**. Reference is
ajouatom/openpilot carrot-wip at 604bc0a22733e648ec05b268da1ffaae7db52a69;
target base is 09f3f58d9f9f7a59d6f983c4e0536c092aab1a4f. The fetched reference
has not moved since the supplied observation. The contract, raw-blob manifest and
provenance document contain the source evidence and interpretation limits.

## What the fixture proves

[carrot_signal_cases.json](carrot_signal_cases.json) contains 16 independent,
hand-authored synthetic evidence specifications. No route, real log, vehicle
identifier or personal data is used. Its metadata explicitly sets
mapping_executed=false. These are not replay inputs, not cereal messages and not
outputs of a mapper. No message-neutral mapper, enum implementation, controller
hook or actual adapter exists in this change. The hard gates prevent starting
the implementation and its TDD mapping tests.

Every case expects REJECT_NO_SNAPSHOT with control_active=None and
controller_saturated=None, even the otherwise normal torque example. A requested
active flag is not final applied authority; a controller's timer alert does not
prove current actuator limiting or its absence. The case_policy_vetoes are local
audit labels, not new runtime ReasonCode members or an implemented veto order.
They distinguish additional defects from the two global semantic blockers.

| Case | Additional evidence/policy veto | Result |
|---|---|---|
| normal_torque | No additional defect; authority and saturation remain unproven | No Snapshot |
| inactive_controller | INACTIVE_REQUEST | No Snapshot |
| unknown_activity | ACTIVITY_UNAVAILABLE; null is preserved | No Snapshot |
| steering_override | DRIVER_OVERRIDE | No Snapshot |
| saturation_alert | SATURATION_ALERT_PRESENT; alert retained as raw evidence only | No Snapshot |
| controller_type_mismatch | CONTROLLER_UNION_MISMATCH; no inferred context | No Snapshot |
| missing_union_state | MISSING_UNION_STATE; no default Bool/zero | No Snapshot |
| stale_carState | STALE_CAR_STATE, EXCESSIVE_TOPIC_SKEW | No Snapshot |
| stale_controlsState | STALE_CONTROLS_STATE, EXCESSIVE_TOPIC_SKEW | No Snapshot |
| excessive_topic_skew | EXCESSIVE_TOPIC_SKEW within otherwise fresh publication ages | No Snapshot |
| canValid_false | CAN_INVALID, INVALID_EVENT | No Snapshot |
| valid_false | INVALID_EVENT | No Snapshot |
| topic_not_alive | TOPIC_NOT_ALIVE, TOPIC_NOT_UPDATED | No Snapshot |
| topic_frequency_failure | TOPIC_FREQUENCY_FAILURE | No Snapshot |
| reordered_timestamp | OUT_OF_ORDER_PUBLICATION relative to supplied previous metadata | No Snapshot |
| immutable_baseline_mismatch | BASELINE_MISMATCH; trusted baseline remains synthetic 10 | No Snapshot |

The independent case index is a candidate attempt label, not a simulated adapter
stream. Repeating the same case data gives the same arithmetic and labels. An
actual adapter must define lifecycle, rejected-cohort identity and high-water
rules before any stream is implemented. No mutation or defensive-copy behavior
of a nonexistent mapper is claimed; the supplied inputs and expected baseline
are unchanged static data. Existing core tests verify their own immutable
Snapshot/result and engine baseline invariants separately.

## Clock arithmetic and limits

All integer timestamps are invented same-domain publication/receive times. Bounds
are explicitly TEST_ONLY_NOT_VEHICLE_DEFAULTS: publication age 0.25 s, receipt age
0.125 s and topic skew 0.125 s. They are not suitable vehicle values or proposed
production defaults. The source contract requires caller-approved policy.

For the base case, publication times are 100 and 100.03125 s, evaluation is
100.0625 s, and receive observation times are 100.046875 s. The publication anchor
is 100.03125 s; age at that anchor is 0.03125 s; engine effective publication age
is 0.03125+(100.0625-100.03125)=0.0625 s. Each receipt age is 0.015625 s.
Do not supply 0.0625 as age-at-anchor and then add elapsed time again. These
figures describe publication freshness, not physical sensor age or proof of
which carState controlsd consumed.

The dead-topic case has an older carState receive observation and no carState
update. The new controlsState receive observation is at evaluation time, so its
known receipt age is zero. The carState receive age is 0.109375 s, exceeding
SubMaster's nominal 10/100 s alive test. This known numeric zero is distinct from
the missing authority/union values, which remain null.

## Static validation method

The audit used standard-library Python outside the package. It parsed the JSON,
checked the 16 case IDs and explicitly expected veto lists, global blockers,
null handling, candidate context/attempt labels, raw flags, trusted synthetic
baseline and absent mapper. It checked all six metrics per case with exact
Fraction(integer_ns, 10**9) equality to the written expected values. It verified
that the input document was unchanged. This is document consistency validation,
not a source consumer or a callable mapping implementation.

For the source evidence it used git show on each of the 37 pinned blobs, verified
byte count, Git blob SHA-1 and raw-byte SHA-256 against the manifest, and checked
52 linked source ranges against their actual line counts. All 13 Snapshot matrix
rows were present. Symbol names were checked against the Python source AST; no
reference module was imported or executed. The static validation result was:

```json
{"mapper_executed":false,"pinned_link_ranges_verified":52,"snapshot_fields":13,"source_blobs_verified":37,"static_cases_verified":16}
```

To independently reproduce the source pin and raw hash check, use a reference
checkout outside this repository and read Git blobs, not worktree bytes:

```sh
git -C ../openpilot-carrot-reference rev-parse origin/carrot-wip
git -C ../openpilot-carrot-reference show 604bc0a22733e648ec05b268da1ffaae7db52a69:openpilot/selfdrive/controls/controlsd.py
```

For each manifest path, hash the stdout bytes of git show with SHA-256, check its
length, and compute Git SHA-1 over b"blob "+ASCII(length)+b"\0"+blob. For each case,
recompute T=max(t_car,t_controls), source_age=T-min(t_car,t_controls),
effective_age=now-min(t_car,t_controls), skew=abs(t_car-t_controls), and each
receipt_age=now-recv_time. Divide integer ns by 10**9 and compare exactly to the
fixture. No source import, network fixture, Params read or adapter execution is
needed. The manifest is the complete file list; do not silently repin to a branch
that moves after this audit.

The source distribution includes docs/*.json so the signal cases and hash
manifest accompany the Markdown evidence. The installed runtime wheel remains
free of reference sources, Carrot dependencies and a mapper implementation.

## Scope and decision

Source inspection finds two semantic blockers; source availability alone does
not resolve them. Clock alignment and full source validity remain conditional
designs, and an immutable caller baseline is a boundary policy, not an approved
vehicle registry. Neither source raw estimates nor Params keys become effective
tuning values. No target LICENSE is selected and no reference code is copied.

The existing regression suite, architecture boundaries, package build and replay
goldens are checked independently of these static cases. Passing them cannot
approve a Carrot mapping. Draft PR evidence and the final report record actual
quality-check results. No Phase 8B, persistence, real logs, Apply or vehicle test
starts after this audit.
