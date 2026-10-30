# Guest closure review and author fix pass

Independent read-only review: **C0/I6/M0**, exact
`2c46625296aa4d257157c447988b3c2b23b184f4` versus base
`9aeb4aeda3297d25b0df7d5dbb909265847f597a`. All six Important findings accepted;
none waived because overall qualification is BLOCKED. The reviewer reran171
focused tests, reproduced24 current image identities/report and the fixed-input
CLI observation. No tracked source or asset was changed by the reviewer.

Before implementation changes, all15 rejection regressions failed RED. One
author fix pass made all15 GREEN and added seven legacy-read boundary tests.
The full suite was rerun. **No independent re-review of the fix head; no C0/I0
independent verdict claimed.** Deferred minors: none.

## Findings fixed (tests/unit/test_guest_closure_review_fixes.py)

- I1 `test_no_legacy_symlink_bytes_are_read_before_anchored_observation`: remove
  legacy vm_runner imports/calls. New bounded/scoped no-follow checks preserve
  pinned4,307/5,501/13 receipts; actual consumed image bytes are checked again.
- I2 `test_nested_parent_replacement_rejects_even_when_root_and_file_descriptor_match`:
  retain/revalidate the parent chain for selected scans and bounded reads.
- I3 `test_unsupported_dynamic_search_flags_cannot_use_default_library_resolution`
  and duplicate-singleton regression: observe DT_FLAGS/DT_FLAGS_1 and reject
  unsupported flags (including NODEFLIB) or conflicting singleton tags.
- I4 `test_zero_filled_or_partial_load_overlap_is_not_unique_dynamic_metadata`:
  check p_memsz intervals, including zero-fill/partial overlap.
- I5 `test_shared_dependency_requires_supported_abi_and_shared_object_role`:
  supported System V/Linux OSABI, version0 and ET_DYN dependencies only.
- I6 `test_bootstrap_node_cannot_be_a_regular_file_or_conceal_a_link_cycle`:
  exact character-node kind/mode/major/minor at both bootstrap paths.

Actual HF01 current-image bytes were also repacked (not executed) with NODEFLIB,
FreeBSD library OSABI and ET_EXEC library substitutions; all three reject. Original
images/snapshot/old manifests/binaries remain unchanged. New ELF metadata includes
ABI/version/flags, and source identities include the new safe legacy reader.

## Exhaustive rulings, in order

1. Inline without repeated design/plan menu: user delegated ordinary work.
   Cost: author-selected architecture.
2. Dedicated checkout/new branch: established workflow.
   Cost: less isolation than another worktree.
3. Manual ledger: cloud helper unavailable. Cost: bookkeeping risk.
4. Separate offline current verifier, no old-manifest edits or rebuild launcher:
   past consumption cannot be invented. Cost: full closure remains BLOCKED.
5. Publish inventory/metadata, not third-party executable images.
   Cost: actual graph recomputation needs prepared assets, unlike normal CI replay.
6. D1 historical build consumption unavailable: current bytes are not past choices.
   Cost: no historical build proof.
7. D2 historical executed-image binding unavailable: reconstruction is current.
   Cost: no retrospective execution qualification.
8. D3 whole host compiler closure unqualified: selected scope disclosed.
   Cost: unknown compiler/header/search dependencies.
9. D4 host Python closure unqualified: no import/interpreter seal.
   Cost: no complete Python/pyc/site/preload assurance.
10. D5 QEMU dynamic inputs unqualified: exact tree is not full consumption.
    Cost: no full hypervisor input closure.
11. D6 arbitrary dlopen/NSS/plugins/shell behavior unqualified: static imports only.
    Cost: no dynamic behavior completeness.
12. D7 execution immutability unproven: observation is not sealing.
    Cost: inputs can change after verification.
13. D8 collector/report authenticity unqualified: UNTRUSTED content identity.
    Cost: coherent forgery not excluded.
14. D9 compromised host/forged metadata/outside-root ancestors excluded; ordinary
    inside-root replacement I2 fixed. Cost: no hostile-host/outer-ancestor guarantee.
15. D10 full executable/relocation/BPF/device validity unqualified: metadata only.
    Cost: no actual execution/device compatibility assurance.
16. D11 untrusted caller reports/fewer-image pure calls diagnostic; explicit counts,
    fixed adapter owns24. Cost: caller reports do not prove authenticity/cohort.
17. D12 reviewer did not rerun full build/wheel/CRLF/remote CI; focused/current
    verification independent. Cost: broad regressions rely on author checks and CI.

Items6–17 cover every declined-to-judge behavior, not silent passes. Exact final
verification/head is in the result document and Draft handoff comment.
