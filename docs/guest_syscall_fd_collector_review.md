# Guest collector independent review and author fix pass

Reviewed exact head: `8f1ac2995d89bb7cc5ba5c4b955768bb6d88c4f8`.
Base: `1b2ff21ac83a8ea9d7c04850c8e2f7e92d06425d`.
Fresh independent read-only reviewer: **C0 / I6 / M0**. The reviewer replayed
all24 committed actual captures and the107 then-current focused tests. All six
Important findings were accepted at that severity; none was waived or downgraded.

The author made one TDD fix pass. Initial reproductions: **24 failed /3 passed**
before any evaluator change. These include mutations of actual HF01 receipts,
not just synthetic examples. Each finding's reproducer now passes. Additional
positive and negative cases pin the deliberately narrower profile. The C
collector, its binary and all actual raw capture bytes are unchanged. The fixes
are pure independent reconciliation; generated manifests bind the new evaluator.
There is **no second independent review of the fix head**. A clean post-fix
suite is evidence of those fixes, not a new C0/I0 review verdict.

| Finding | RED reproduction / fix |
|---|---|
| I1 terminal semantics | `test_nonreturning_exit_cannot_have_a_successful_return`, `test_signal_abort_must_match_actual_terminal_wait_status`, `test_normal_exit_status_must_match_the_nonreturning_exit_argument`, `test_execution_cannot_resume_after_terminal_stop`, `test_normal_exit_requires_an_observed_exit_call_not_just_matching_counters`: bind ABORT cause, exit argument, terminal stop and decoded wait status; prohibit resumed execution and successful returns from exit/exit_group. Signal death without a pending syscall remains valid. |
| I2 exec identity/checkpoint | `test_successful_exec_requires_a_generation_event`, `test_exec_fd_checkpoint_is_required_and_bound_to_that_exec_call`: successful exec requires exactly one generation event and that call's post-exec FD checkpoint. Failed/nonzero exec cannot claim success. Old, duplicate or cross-call FD checkpoints cannot replace the first captured table. |
| I3 clone flags | `test_birth_flags_cannot_override_unsupported_flags_in_parent_clone`, `test_clone3_pointer_is_not_a_substitute_for_separately_observed_flags`: compare birth flags with actual parent entry; reject shared/thread/untraced flags from entry itself. Successful clone3 has unavailable pointee flags in this wire profile and cannot qualify FD completeness. |
| I4 x32 execution | `test_successful_x32_execution_is_not_a_native_fd_profile`: successful x32 is not native-x86_64 execution. A rejected x32 attempt remains observable, including actual HF09. |
| I5 complete FD delta/dup provenance | `test_scalar_acquisition_cannot_change_an_unrelated_existing_fd`, `test_dup2_result_must_be_the_requested_destination`, `test_duplication_target_must_match_source_object_and_flags`, `test_status_only_seccomp_or_bpf_call_does_not_acquire_a_scalar_fd`: require exact destination, source object/flags and no unrelated changes; distinguish FD-producing seccomp/BPF operations from status operations. |
| I6 ADDFD flags | `test_addfd_flag_dependent_fields_must_match_the_observed_target`: require supported atomic-SEND profile, zero ignored newfd, valid newfd_flags and exact target CLOEXEC/non-CLOEXEC flags. Count a donation only after contextual checks; no-CLOEXEC delivery remains valid when its actual target agrees. |

The two `test_actual_hf01_cannot_be_made_complete_with_contradictory_receipts`
cases also changed RED→GREEN: replacing nonreturning ABORT with successful RETURN,
or changing donation flags while retaining the original target table, rejects.

## Rulings made, in order

1. Continue inline without another design approval menu: user delegated ordinary
   choices. Cost if wrong: architecture was selected by the author, not the user.
2. Reuse the dedicated checkout on a new branch: consistent with the established
   workflow. Cost: less filesystem isolation than a separate worktree.
3. Maintain the plan ledger manually outside Git because the cloud skill helper
   resource was unavailable. Cost: manual bookkeeping risk.
4. Use ptrace, not BPF syscall tracepoints, as primary observer: exact kernel
   ordering places seccomp rejection before trace_sys_enter. Cost: scheduling
   perturbation; no production timing/performance qualification.
5. Bound completeness to native x86_64 with independent FD tables and supported
   operations. Cost: no general arbitrary-thread/hostile FD/OFD completeness proof.
6. Stop unsupported shared/thread/untraced clone calls before they execute: they
   can escape birth tracing or mutate shared FD state. Cost: unsupported programs
   are not observed unperturbed; no syscall return is fabricated.
7. Demultiplex only complete JSON followed by a timestamped kernel diagnostic on
   the existing console. Cost: internal/unknown interleaving still rejects; no
   repaired or silently discarded capture bytes.
8. Retain reusable source/build/raw-log caches and remove only transient ledger/
   review-package files. Cost: disk usage; no shared VM/setup assets are deleted.
9. Leave mutually consistent malicious collector replacement/authenticity
   unqualified: reports explicitly remain UNTRUSTED and consistency is not trust.
   Cost: no collector authenticity guarantee.
10. Leave absolute clock authenticity/external drift unqualified: the explicit
    clock is observer time, without an external reference. Cost: no external
    clock or controller-timing assurance.
11. Leave initial seed-FD alias deduplication unqualified: observations start
    after those acquisitions. Cost: no complete initial OFD deduplication proof.
12. Leave arbitrary concurrent pidfd target mutation unqualified: fixed tested
    targets are blocked, not general mutating FD tables. Cost: no general
    concurrent-target provenance guarantee.
13. Leave unperturbed unsupported clone execution unqualified: capture stops
    before shared/thread/untraced calls. Cost: the bounded profile cannot support
    claims about those programs' original behavior.
14. Leave complete compiler/static-loader closure and malicious-cache resistance
    unqualified: content hashes are not a trusted build/host TCB proof. Cost:
    those inputs and their origin still need a separate qualification task.
15. Do not request new VM/device/native execution from the reviewer: read-only
    review replays author-collected evidence. Cost: no independent fresh guest
    execution and no physical-device qualification.

Items9–15 are the reviewer's explicit declined-to-judge list, accepted as scoped
limitations by the author, not silently treated as passed checks.

Deferred minors: **none (M0)**.

## Post-fix verification

All24 original raw captures still reconcile, with identical digests and metrics:
136,933 events;81 task lifetimes;66,562 syscall returns;80 aborted/nonreturning
calls;25 execs;3,520 FD transitions;14 notifications;4 donations. The compressed
raw artifact is byte-identical. No producer was rerun or historical receipt
promoted. Global prohibited-effect/handle counts remain null; permissions false.

Exact final test counts and coverage are recorded in the result document.
Exact-head push and pull-request checks are reported on the new stacked Draft.
No prior branch/PR, installed package, source fixture, replay golden or CI changed.
