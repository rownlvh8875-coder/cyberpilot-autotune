# CyberPilot native E — Cloud continuation handoff

Date: 2026-11-06
Repository: https://github.com/rownlvh8875-coder/cyberpilot-autotune
Published branch: research/native-e-cloud-handoff-20261106
Entry point: this file, then CLOUD_NEXT_TASK.md and AGENTS.md.

## What was handed over

This is a **standalone research snapshot**, not the product tree and not a product integration.
It has an independent root Git history. Do not merge it into main, PR8, or PR9.
The product main observed at handoff is 4b77b31dd23010f2d2b394466d88b04a4a2720e2.
The original local research revision is f9490bb7d3d1b605f309cde5441ca3f561969325.
All 135 tracked files at that research revision are copied byte-for-byte.
CLOUD_SOURCE_MANIFEST.json binds their SHA256, Git blob identity and mode.
The original local Git history and private evidence remain local; this snapshot does not prove their ancestry.
The verifier checks workspace byte consistency, not authenticity, custody or execution authorization.

The product's frozen path/history guards remain unchanged in its own tree.
An independent research branch avoids widening those guards or treating research code as a provider.
The old README.md describes an earlier direct-child profile; use the later reports below for current status.

## Read in this order

1. AGENTS.md and CLOUD_NEXT_TASK.md.
2. PLAN.md and PROGRESS.md, starting from the most recent completion entries.
3. LOCAL_FACTORY_INTENT_REPORT.md, FACTORY_INTENT_DESIGN.md, FACTORY_INTENT_REVIEW.md.
4. FACTORY_MANAGER_DESIGN.md and research/factory_manager/{factory.c,request.c,internal.h,sdbus_abi.h,unbound.c}.
5. LOCAL_REAL_CGROUP_REPORT.md, REAL_CGROUP_DESIGN.md, COHORT_INTEGRATION_DESIGN.md.
6. ADMIN_CHANGE_REVIEW.md, ADMIN_CHANGE_TRANSACTION.md and ADMISSION_FENCE_CUSTODY_ADR.md as blocked proposals.

Do not restart completed environment/provenance surveys. Do not mistake older unchecked plan boxes for pending work:
later completion entries are authoritative. Preserve old reports, source and tests; append to the existing ledgers.

## Completed local research

- Fixed bootstrap, bounded framing/EOF/FD lifecycle, parent grant and sealed fixed-worker entry.
- Native private sd-bus manager fixture: synthetic M owns E; F never adopts E pidfd.
- E-created D with original W birth/stop/wait/reclaim in regular-file simulations.
- Two serial real cgroup2 user-unit labs: positive kernel path and expected pre-exec source-drift denial.
- Persistent native factory intent before manager request: O_EXCL, bounded write/readback, file/root fsync.
- Concurrent claimants, crash/restart denial, receipt non-authority, partial/unknown I/O, FD reuse and expiry fixtures.

Latest local CPU/POSIX evidence: **647 unique PASS /0 FAIL/0 SKIP =586 preserved +61 new**.
This is the union of a 646-case full run and a final 61-case focused run, with 60 overlaps removed.
It is not a single 647-case pytest invocation. UBSan61 and GCOV61 are repeats and are not added.
Old Python coverage91.74% at unchanged90% threshold. Native intent lines100%, branch outcomes74.68%;
coordinator lines100%, branch outcomes89.47%. Ruff/format76 files and existing mypy14 modules passed.
Historical product2786PASS is NOT_RERUN and not added to this total.

These are prior local observations, not Cloud pass counts. Re-run only the relevant classes actually supported here.
The final anchor repair intentionally leaves terminal reference slots until process exit:
native_release=PARTIAL_REFS_RETAINED, not whole-HOST cleanup confirmation.
Unknown/uninspected intent durability is null; it is not filled with false.
The test-only pause child has a fixed4s alarm even if its harness disappears.

## Real OS facts do not transfer to Cloud

The local host was unprivileged Ubuntu-24.04 WSL2/x86_64 with CapEff0.
The real labs were fresh separate attempts; user-manager PID/starttime differed between WSL calls.
Cause remains UNKNOWN. Each attempt preserved its before/after identities and controller configuration.
Do not claim the same namespace/generation or investigate/clean old residue from Cloud.

The inner manager remains synthetic. Credential mutation was a no-forward test shim.
Protected factory/code/loader origin, real cross-UID sealing, original protected F1 custody,
readonly mounts, namespace containment and external-writer/async drain remain unimplemented or unqualified.
A manager-created external P is not an E-created D; E must remain outside the D it stops.

## Safe Cloud setup

Use a fresh dedicated checkout/worktree of this published research branch. Never overlay the product checkout.
Verify the expected published commit supplied in the Cloud task prompt, then:

```sh
python3.12 -I -B CLOUD_VERIFY.py
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

Use only an already available Python>=3.12.3,<3.13 and existing compiler/runtime libraries.
A new workspace venv install is allowed. No sudo, root-account workaround or system package install.
If Python/GCC/libsystemd or native kernel permissions are unavailable, record the exact blocker;
continue independent pure parsing/type/unit-test work without weakening the baseline.
If the Cloud executor is already UID0, do not run the native F/E/W or unit/cgroup experiments as root.
Do not create a user, change UID or permissions to evade that gate.
Pure value/encoding/source tests and compilation can proceed without converting them into native execution evidence.

For supported nonroot native fixtures, use a new private basetemp outside the checkout on every run:

```sh
.venv/bin/python -m pytest -q --cov=native_e_lab --cov-branch --cov-fail-under=90 --basetemp=<new-private-path>
.venv/bin/python -m pytest -q tests/test_factory_intent.py --basetemp=<another-new-path>
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
MYPYPATH=src:. .venv/bin/python -m mypy --explicit-package-bases -p native_e_lab -p research.real_cgroup -m research.admin_review.check_bundle
```

Do not call run_user_lab(), run_fixed_real_lab(), systemd-run, arm anything or reattach from old receipts.
Those code paths are present as historical research, not newly authorized Cloud OS experiments.
No WSL, laptop, comma or Jetson connectivity is needed for the next coding task.

## Publication and authority boundaries

Included: source/tests, sanitized reports/designs/evidence, append-only progress, this handoff and byte manifest.
Excluded: .git history, .venv, binaries, bundles, caches, raw private logs, actual lab kits, fixture residues,
original intent files, personal paths, credentials and any vehicle data.
IPv4-shaped hits in the reviewed source were kernel version components, not device addresses.

Provider registration remains UNBOUND. Required16 qualification evidences remain UNAVAILABLE/available0.
All14 admission/qualification flags remain false; no approval or recovery record is created.
This handoff authorizes research development only. No actual H/product/vehicle payload is released.
Next implementation scope is exactly CLOUD_NEXT_TASK.md; no manager/admin deployment is included.

Publication check note: old Markdown hard-break trailing spaces are preserved with the original135 byte identities.
A root-commit whole-tree git diff --check reports those historical lines; the six newly authored handoff files pass separately.
No original source or test was normalized to suppress that report.
