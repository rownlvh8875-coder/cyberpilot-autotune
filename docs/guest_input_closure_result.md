# Guest-only input closure verifier — implemented, full closure BLOCKED

2026-10-30 (Asia/Seoul). Base PR28
`9aeb4aeda3297d25b0df7d5dbb909265847f597a`.

## Outcome and limits

Implemented a separate **read-only offline verifier** for the approved fixed
harmless software guest. Current11,351 declared input entries match; all24
reconstructed images pass the fixed static ELF-import namespace profile, each
with32 members and15 dependency/interpreter/shebang edges. This task ran **no
compiler, loader, QEMU, guest, Carrot-native, model, device or vehicle payload**.
Python verification/tests/build and passive offline source regressions are not
target execution. Old source, evidence, binaries, installed package, CI and
PR8/9/25/26/27/28 are unchanged.

The overall result is deliberately **BLOCKED**, not full input closure READY.
Existing binaries were produced earlier without a complete consumed-build-input
receipt. Today's matching bytes cannot reconstruct those historical choices or
seal mutable inputs during a future execution. Frozen Python contracts are
immutable values; **the observed filesystem is not proved immutable**.

`UNTRUSTED_CURRENT_CLOSURE_REPORT` is content evidence only. The two narrow facts
`declared_inputs_match` and `guest_elf_dependencies_closed` neither authenticate
the collector nor authorize execution/application. All seven runtime/device/
policy/candidate/application/owner permissions stay false, global prohibited
handle/effect counts stay None. Prior HF reports are never upgraded to PASS.
STRICT_NO_DEVICE_ATTEMPT remains; Gate A BLOCKED and B/C/D not started.

## Current input inventory

| Logical root | Coverage | Entries |
|---|---|---:|
| toolchain_exact_tree | Exact cached toolchain tree | 5,782 |
| vm_exact_tree | Exact cached VM sysroot tree | 5,502 |
| repo_selected | 28 selected source/manifest files + root mode | 29 |
| kernel_selected | 8 studied source files + root mode | 9 |
| fixture_selected | 3 existing outputs + root mode | 4 |
| collector_selected | Existing collector + root mode | 2 |
| host_gcc_selected | 22 selected GCC/linker/CRT/archive paths + root mode | 23 |

Each exact tree includes its root directory, hence the extra entry compared with
descendant-only inventories. Selected paths are **not whole directory, compiler,
Python import or search-path closure**. The original4,307-input manifest,
5,501-entry VM tree and13-input collector manifest are separately verified before
image reconstruction. None is edited or retrospectively strengthened. After
independent review, this is done by the new bounded/scoped no-follow legacy
reader, not by importing old vm_runner code. Raw legacy manifests are pinned
before their paths are interpreted; the canonical VM receipt is pinned too.
Image-builder asset bytes are checked again against their observed identities.

Canonical snapshot digest:
`6f854b3c1e6bb1f216092c87f983c553a7ff5419897415f56a007d74e06b5eb7`.
The456,312-byte compressed inventory binds actual kind/mode/size/hash or literal
symlink target. Paths are logical root + normalized relative name, never inferred
from a branch/PID/object address. New/missing paths in exact trees reject. SHA-256
is content identity, not trusted provenance or permission.

Linux filesystem reads anchor descriptors with O_NOFOLLOW, compare actual
file/directory identity before/after, retain/revalidate the parent bindings, and
never follow observed host symlinks inside the anchored roots.
Hash reads stop beyond the initial size; directory names are bounded before
sorting. Bounds:50,000 entries,64 directory depth,1GiB/file. Before/after checks
catch ordinary instability but **not malicious-host/ancestor replacement or
execution-time TOCTOU**. No chmod/mount/security policy is applied.

## Guest static loader profile

The verifier parses bounded gzip/newc bytes without extraction or mknod. It
rejects duplicate/traversal names, hardlink ambiguity, malformed/truncated or
concatenated images, unsupported owners/types and unknown namespace members.
The two bootstrap console/null pseudo-nodes remain metadata, never physical
device tests. A fixed32-member namespace excludes preload/cache/hwcaps additions.

ELF64 little-endian program headers provide PT_INTERP, DT_NEEDED, SONAME and
RPATH/RUNPATH/audit/config/filter directives. No ldd/loader invocation, section-name
guessing or binary execution occurs.10 native x86_64 ELF objects and1 separate
BPF relocatable object are observed. Libraries resolve only in the archive's
`/lib/x86_64-linux-gnu`; the interpreter resolves through its actual guest link.
Missing/wrong ABI/type/SONAME, alternative search/audit/filter paths and wrong
bootstrap objects reject. Component-wise link resolution preserves ENOTDIR-like
semantics: `file/../other` is not lexically simplified into a valid code object.
Supported OSABI/version and ET_DYN dependency roles are explicit. DT_FLAGS and
DT_FLAGS_1 are observed; unsupported search flags including DF_1_NODEFLIB and
duplicate singleton flags reject. Load-memory overlap checks include p_memsz
zero-fill, not just file-backed ranges. Bootstrap node paths require their exact
character-node kind/mode/major/minor, never a self-link or regular substitute.

The current15-edge graph includes fixture→libbpf/libc, libbpf→libelf/libz/libc,
libelf→libz/libzstd/libc/loader, libc→loader and init→busybox. Static executables
have no invented interpreter. This is **static ELF imports plus the named init
interpreter**, not arbitrary dlopen/NSS/plugins, shell semantics, dynamic code or
full execution behavior. The corresponding blocker remains explicit.

## Historical versus current evidence

All24 images are **CURRENT_RECONSTRUCTION_NOT_HISTORICAL_CONSUMPTION** from the
unchanged pinned cached assets and existing pure builder. Image digests,11 ELF
metadata/object hashes and the new inventory are published in
[machine-readable evidence](evidence/guest_input_closure_result.json).
No old capture digest is bound to a newly invented build/exec receipt.

Third-party executable images/binaries are not newly redistributed. Ordinary CI
replays the committed inventory/metadata and synthetic byte-parser adversaries;
it cannot recompute the actual ELF graph without the prepared local cache. The
explicit fixed read-only verifier performs that recomputation and returns a
precise UNAVAILABLE if assets are absent/drifted, without download or substitute.
It requires the pinned Linux exact-byte checkout; CRLF normalization is never
used to silently equate different consumed source bytes.

## Operation and verification

Default `python -m compatibility.guest_input_closure.host_main` exits2 without
observing files. Only `--verify-current` reads the fixed selected roots. No
arbitrary command/root, blessing mode, background process, thread, subscriber,
network or file-write API. The explicit verification also exits2 while overall
BLOCKED, even if both narrow facts are true. This is fail-closed behavior, not a
failed target execution. The package is outside the installed wheel.

TDD covered missing APIs/evidence, real tmpdir content/mode/link/add/remove drift,
growth during hashing, symlink substitution/cycles/escape, malformed ELF/string/
archive boundaries, unsupported search paths and fixed-false authority. A second
process compared the frozen current snapshot with newly observed fixed inputs;
both narrow facts were true, issues empty and overall BLOCKED as intended.
Exact final regression, coverage, review and exact-head CI results are recorded
on the new Draft and in the review record; no producer boolean substitutes for
those checks.

Before independent review: **2,175 full tests /171 focused tests pass**. Pure
verifier unit coverage:99.32% statements /98.28% branches (targets95%/90%). Entire
new package combined unit+actual-read-only verification coverage:96.13%; filesystem
adapter alone86.93% combined. No target/C/BPF execution-coverage claim. Global
ruff/format, strict mypy (80 source files), build and fresh empty-venv vanilla+
research wheel/replay/knowledge/owner/science/friction/receipt smokes pass.
Historical source/history audits and passive offline native192 pass. A fresh
fixed-input re-observation in another process exactly matched the published
report, including all24 reconstructed images; exit2/BLOCKED is intentional.

Post-review: **2,197 full tests /193 focused tests pass**. All15 counterexample
regressions changed RED→GREEN in one author fix pass, with seven additional safe
legacy-read tests. Actual current HF01 bytes repacked with NODEFLIB, FreeBSD ABI
and ET_EXEC library substitutions now reject without execution. A new fixed-input
observation still exactly matches the original snapshot/image identities/report.
Pure unit coverage:99.13% statements /97.97% branches. Entire package unit+actual
read-only combined coverage94.28%; filesystem87.39%, legacy adapter84.34% combined.
Strict mypy now covers81 source files. These are Python verification metrics,
not target-execution or immutable-host qualification.

Independent review at exact2c46625296aa4d257157c447988b3c2b23b184f4 was **C0/I6/M0**.
All6 Important findings were fixed and the full suite rerun. **The fix head was
not independently re-reviewed; no C0/I0 verdict is claimed for it.** All rulings,
fixes and declined-to-judge costs are in the [review record](guest_input_closure_review.md).
Deferred minors: none.

## Status and blockers

```text
GUEST_INPUT_INVENTORY_VERIFIER_IMPLEMENTED
GUEST_STATIC_ELF_IMPORT_PROFILE_VERIFIED_CURRENT_RECONSTRUCTION
GUEST_FULL_INPUT_CLOSURE_UNQUALIFIED
HISTORICAL_BUILD_CONSUMPTION_UNPROVEN
HISTORICAL_EXECUTED_IMAGE_BINDING_UNPROVEN
HOST_COMPILER_CLOSURE_UNQUALIFIED
HOST_PYTHON_CLOSURE_UNQUALIFIED
QEMU_DYNAMIC_INPUTS_UNQUALIFIED
DYNAMIC_LOAD_BEHAVIOR_UNQUALIFIED
EXECUTION_INPUT_IMMUTABILITY_UNPROVEN
COLLECTOR_AUTHENTICITY_UNQUALIFIED
GATE_A_BLOCKED_DEVICE_PROBE_CONTAINMENT_UNRESOLVED
FRICTION_RUNTIME_PRODUCER_NOT_DEPLOYED
FRICTION_RUNTIME_PRODUCER_NOT_QUALIFIED
INSTRUMENTED_NATIVE_RUNTIME_SOURCE_REGISTRATION_UNQUALIFIED
FRICTION_EMPIRICAL_IDENTIFICATION_NOT_QUALIFIED
FRICTION_OBSERVATION_ELIGIBILITY_BLOCKED_MISSING_Q
REPRESENTATION_ENCODING_RUNTIME_UNQUALIFIED
NO_EMPIRICAL_ESTIMATOR_BRIDGE
FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
FACTOR_IDENTIFICATION_UNQUALIFIED_FROZEN_DEVELOPMENT_ARTIFACT_UNAVAILABLE
PARAMETER_IDENTIFICATION_QUALIFICATION_UNRESOLVED
VEHICLE_APPLICATION_BOUNDS_UNRESOLVED
RUNTIME_FINGERPRINT_UNCONFIRMED
WATCHDOG_EXECUTION_MODEL_UNRESOLVED
EXTERNAL_EXECUTOR_UNQUALIFIED
APPLICATION_NOT_AUTHORIZED
```

Recommended next **single** task: **guest-only hermetic build-consumption and
input-promotion receipt design**. New, explicitly bound build inputs and a reviewed
promotion boundary are needed; current hashes cannot retroactively supply them.
No implementation/execution of that next task starts in this handoff.
