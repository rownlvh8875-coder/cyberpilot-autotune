# Hyundai / Santa Fe override capability

## Authority and source qualification

The owner authorized Phase 8B.1H on the existing PR #7 branch, append-only,
starting at cad4ad31e72956d8c73c5d77f58fe6ee8b7d375a. Base/main remains
16e1695e7a9b41f4a6bc728a5bca781d38b26151. Initial PR state is Open/Draft,
mergeable, with all ten push/PR checks successful and no unresolved thread.

Reference source is c2130730239bcdb4cbde9361ab90c8d99aa4ff55 in
rownlvh8875-coder/openpilot. Integration merge
7a2f051b1f3847786318900444c88c2ba7a74a67 has the same tree; the original
base is 604bc0a22733e648ec05b268da1ffaae7db52a69. No reference code changes.

[Source evidence](evidence/hyundai_santafe_override_capability.json) records raw
file and exact LF byte-range SHA-256 hashes, symbols, branch dispatch, assignments
and normal return locations. No upstream source body is copied or executed.

| Variant | Entry / assignment | Decoded driver torque | Availability evidence |
|---|---|---|---|
| Legacy | CarState.update / CarState.update | MDPS12.CR_Mdps_StrColTq | Unconditional steeringPressed assignment at line 552 before normal ret return at 696 |
| CAN-FD | CarState.update / CarState.update_canfd | MDPS.STEERING_COL_TORQUE | CANFD dispatch at 506-507; unconditional assignment at 1396 before ret return at 1625 |

Both producers call CarStateBase.update_steering_pressed with the absolute torque
threshold predicate and min-count 5. The helper asserts after six consecutive
true predicates, saturates its counter at six, and clears immediately on a false
predicate. There is no separate amplitude hysteresis. Existing upstream thresholds
are recorded only as provenance; this package neither reproduces the filter nor
adds a tuning threshold. No torque-in-Nm or physical authority claim is made.

HyundaiFlags.CANFD is `2 ** 13 = 8192` in the pinned values.py, not an inferred
bit. HYUNDAI_SANTA_FE_2022 is HyundaiPlatformConfig, documented as Hyundai Santa
Fe 2021-23, with CHECKSUM_CRC8 (65536) and no CANFD bit. It follows the legacy
producer. HyundaiFlags.LEGACY is a separate safety flag; absence of CANFD chooses
this parser path regardless of that differently named flag.

HYUNDAI_IONIQ_5 is the narrow additional CAN-FD qualification fixture:
HyundaiCanFDPlatformConfig.init adds CANFD to EV, giving static flags 10240.
It qualifies the other requested producer branch, not the owner's vehicle.

## Design and runtime attestation

Ruling: choose **Option B**, an optional ProducerAttestation.platform_key supplied
from runtime CP.carFingerprint. Brand/flags alone cannot bind a Santa Fe claim.
The allowlist contains only the two inspected platform keys above. This costs an
explicit caller attestation; unrecognized platforms fail closed until audited.

Keep the existing three-field SteeringPressedCapability API and Tesla/VW behavior.
Extend supports with an optional platform_key keyword. Hyundai additionally
requires the pinned revision, exact Hyundai source path, matching assignment
symbol, required source static flags, and platform-consistent CANFD bit. Extra
dynamic flags do not replace required static flags. Unknown platform metadata is
rejected; absent/unconfirmed metadata cannot make scalar False known. The frozen
attestation is checked on extraction. Changing it requires the existing explicit
new-session reset; it is never inferred from incoming carState or a vehicle name.

Platform strings are non-identifying source enum names. The pinned Platforms
implementation uses the enum name as its string value; CarInterfaceBase assigns
the candidate to CP.carFingerprint and carries source flags into CP.flags.
No CP/Params reader or runtime identification mechanism is implemented here.
The caller must bind context and platform metadata to the same qualified CP and
producer session. This boundary does not authenticate a caller or remote sender.

**SOURCE_PLATFORM_QUALIFIED** describes the source platform only.
**RUNTIME_FINGERPRINT_UNCONFIRMED** describes the owner's vehicle: no actual
CP.carFingerprint has been supplied or observed. Its model/year/trim does not
force a fingerprint. A mismatched or unconfirmed fingerprint prohibits mapping;
synthetic test attestations do not confirm the owner's vehicle.

steeringPressed is a filtered driver lateral override observation. It proves
neither physical steering authority nor that the vehicle followed a command.

## Execution plan and verification ledger

- [x] Recheck exact PR #7/base/head/CI and unchanged integration merge.
- [x] Audit both normal assignment/return paths, source flags, Santa Fe platform,
  enum-string and CP provenance; freeze hashes without source-body copying.
- [x] TDD: actual generated-reader False/True, missing/mismatched capability,
  variant/context/platform mismatch, unhealthy/missing exact source and immutable
  extracted evidence. Preserve all existing 69 literal and 103 schema cases.
- [x] Implement minimal capability and frozen caller platform attestation;
  retain generic API compatibility and no new control/IO capability.
- [x] Verify source hashes in the offline compatibility runner, installed-wheel
  Hyundai mapping, unchanged replay goldens, regression/coverage/lint/type/build.

The final publication gate is a fresh independent whole-PR review at the final
exact head. A Critical/Important finding requires correction with RED/GREEN and
another fresh review. Require all exact-head push/PR checks and no unresolved
thread before Ready/guarded merge commit; then verify parents, ancestor, tree
equality and full main regression. PR metadata and the final report carry that
external review/CI/merge evidence without a self-referential documentation SHA.

Review focus: a default Bool False without qualified capability; legacy/CAN-FD
cross-approval; unconfirmed or wrong platform metadata; repaired rejected cohort
and masked clock/controller faults; expired reader or unhealthy latest-source
substitution. Tests exercise observable decisions rather than source text.

No live SubMaster, engine/learner, persistence, Apply, Params access, real logs,
vehicle installation/test or upstream PR is authorized. Phase 8B.2 is not started.

## Implementation evidence

The new platform-key API was absent at RED. After adding that interface, four
actual-reader False/True scenarios failed because Hyundai evidence remained
unavailable. The minimal source/flags/platform qualification made them pass.
Six further actual-reader scenarios then failed because unhealthy or invalid
source entries still stored known False. Extraction admission now requires both
the frozen transport health and source Event.valid before setting the capability
flag. Such entries retain None/False and cannot produce a Snapshot.

Local verification: 738 base tests; 872 combined tests with zero failures/skips.
The compatibility portion contains the existing 103 checks unchanged, 29 new
Hyundai generated-reader scenarios, and two source-evidence checks. All 69 literal
projections remain unchanged. Native branch-inclusive coverage is 98.82% overall,
98.84% for integrations.carrot, and 97.70% for its state adapter. Ruff/format and
strict mypy pass. Wheel and sdist build; fresh no-openpilot wheel returns the
typed dependency error, while a separate actual-schema wheel verifies generic
mapping plus four Hyundai False/True mappings with immutable baseline. Both
installed wheels verify all four unchanged replay goldens.

Source hashes and inspected ranges are verified before the offline suite. CI
prepares only the additional pinned source files during setup and imports none
of the Hyundai producer code. These tests qualify extraction and attestations,
not live CAN parsing, hardware, or the owner's actual fingerprint.
