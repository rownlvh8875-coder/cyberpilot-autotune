# Porting inventory and provenance

Audit date: 2026-10-28. Source: https://github.com/rownlvh8875-coder/CyberPilot

## Unavailable required baseline

Required pinned commit: `588d6baff90d5ed839b41554f447f12c7f23bed3`.
`git fetch origin <SHA>` returned `not our ref`. GitHub fetch_commit returned
422, `No commit found for SHA`. No checkout or content audit of that object was
possible. It has not been replaced by branch HEAD. This is a Phase 0 acceptance
blocker, not a reason to enable an unsafe fallback or stop independent code.

## Supplemental HEAD review (not the pinned audit)

H = `588d6b21c21089065a7d9165d6e7a438e8aa6297`, observed remote
feature/cyber-autotune HEAD; commit date 2026-10-26, subject
`ci(cyberpilot): add exact27 shadow boundary qualification`.
Paths below came from ls-tree, git grep and git show at H. Existing tests were
inspected by path but were not executed; none of their results are claimed.
P = openpilot/tools/cyber_autotune/; T = P + tests/.
Root LICENSE is MIT, copyright Comma.ai (2018). That root notice alone does not
establish authorship/provenance of each later CyberPilot addition. No source,
tests, constants or documentation were copied. REWRITE means the responsibility
is independently reimplemented from the user specification, not translated code.

| Source path | Commit | Responsibility | Dependencies | Existing tests | Provenance/license | Disposition | Reason | Risk |
|---|---|---|---|---|---|---|---|---|
| Requested pinned tree (unavailable) | 588d6baff90d5ed839b41554f447f12c7f23bed3 | Required original audit | Unknown | Unknown | Unverifiable | UNKNOWN | Object unavailable through Git and API | Cannot certify pinned audit |
| P/contracts.py | H | Offline metric/unit/hash contracts | cyber_lateral command_domain, metrics | T/test_contracts.py | Root MIT; addition attribution unverified | REWRITE | Vehicle parameter families and metric contracts do not match generic snapshots | Type and unit coupling |
| P/profiles.py | H | Pure proposal assessment | contracts, policy, fractions, hashes | T/test_profiles.py | Root MIT; addition attribution unverified | REWRITE | Keep proposal concept; define independent typed contracts | Asserted metadata is not authority |
| P/policy.py | H | Parameter policy registry | contracts, vehicle source paths | T/test_policy.py | Root MIT; addition attribution unverified | REWRITE | No actual vehicle IDs/constants admitted | Incorrect policy reuse |
| P/shadow.py | H | Offline bounded window sessions | threading, monotonic, native_runner/protocol | T/test_shadow.py, test_shadow_noninterference.py, test_shadow_accounting.py | Root MIT; addition attribution unverified | REFERENCE_ONLY | Owns native worker sessions and queues; does use monotonic time | Not synchronous core; OS scheduling |
| P/native_worker.py | H | Native controller experiments | numpy, opendbc, CarInterfaceBase, LatControlTorque | T/test_native_worker.py | Root MIT plus native dependencies; not individually resolved | REJECT | Imports vehicle controllers, subprocess and filesystem paths | Controller state and platform coupling |
| P/native_runner.py | H | Native worker supervision | subprocess, native protocol | T/test_native_runner.py | Root MIT; addition attribution unverified | REJECT | No process or real controller execution in milestone | Deadline and process complexity |
| P/replay_input.py | H | Sealed authorized input snapshots | fcntl, memfd, subprocess, replay_admission | T/test_replay_input.py | Root MIT; addition attribution unverified | REFERENCE_ONLY | Linux IO and admission belong to later replay | Platform and data-access scope |
| P/archive.py | H | Immutable offline archive | ctypes, fsync, locks, archive_codec, profiles | T/test_archive.py | Root MIT; addition attribution unverified | REFERENCE_ONLY | Persistence deferred; no disk IO in runtime | Filesystem assumptions |
| P/synthetic_lateral_gate.py | H | Synthetic offline lateral gate | Offline experiment stack | T/test_synthetic_lateral_gate.py | Root MIT; addition attribution unverified | REFERENCE_ONLY | Different counterfactual experiment contract | Cannot infer vehicle safety |
| openpilot/selfdrive/controls/lib/cyber_lateral/optimizer.py | H | Offline experiment orchestration | experiments, speed tune, steering rate, torque authority | P tests/test_synthetic_lateral_closed_loop.py | Root MIT; addition attribution unverified | REJECT | Includes controller-domain variants outside Phase 0-4 | Vehicle constants and semantics |
| docs/cyberpilot/changes/cyber-autotune-contracts-v2.md | H | Existing contract rationale | Metric/evidence suite | Documentation | Root MIT; addition attribution unverified | REFERENCE_ONLY | Supplemental conceptual comparison only | Not pinned evidence |
| docs/cyberpilot/changes/cyber-autotune-offline-archive.md | H | Offline archive design | Linux archive implementation | Documentation | Root MIT; addition attribution unverified | REFERENCE_ONLY | Defer to persistence phase | No transfer of guarantees |
| LICENSE | H | Root license notice | None | N/A | MIT, Comma.ai 2018 | REFERENCE_ONLY | Record notice without choosing target license | Per-file provenance remains unresolved |

Classification counts (table rows): UNKNOWN 1, REWRITE 3, REFERENCE_ONLY 7,
REJECT 3, REUSE 0, REFACTOR 0. Counts cover selected reviewed responsibilities,
not the entire source tree. Reused files: none. Independently rewritten target
responsibilities: contracts, proposal assessment and generic registry/gate policy.

## Call relationships and audit questions

profiles imports contracts and policy. contracts imports cyber_lateral metrics
and command_domain. shadow calls native_runner, which supervises native_worker;
the worker constructs native controller state for offline runs. That path is not
evidence of live application. It would nevertheless introduce controller
capabilities into this library, so it is excluded. archive imports profiles and
archive_codec and writes local disk. replay_input uses OS descriptors and sealed
memory. The new runtime has none of these IO or lifecycle paths.

Pure validation portions exist, but their openpilot namespace imports and
vehicle-bound units make direct copying unsuitable for small independent PRs.
policy has module-level immutable PARAMETER_POLICIES; no global learner state
is carried into the target. shadow explicitly uses monotonic; no claim is made
that every existing module avoids wall clock. Safety/evidence policy is spread
across profiles, policy, contracts and native workers. Offline replay is separated
from active control in inspected docstrings, but cannot be treated as this new
framework's runtime gate or watchdog.

Searches included autotune, auto tune, online, adaptation, learner, learning,
proposal, safety gate, sanitizer, rate, rate budget, r policy, shadow, replay,
source schema, controller, lateral, longitudinal, rollback, watchdog, persistence,
state and candidate. Exact `F-60` through `F-69` labels were not found by
`git grep -n -E 'F-6[0-9]([^0-9]|$)' H -- '*.md'`. No mapping of those requested
labels to guessed files is asserted. This does not establish their absence at
the unavailable pinned commit. Source-schema/rate-policy concepts occur in the
much larger offline tool suite; exhaustive historical qualification is deferred
until the required object is supplied.
