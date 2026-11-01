# DENY-FD v2: source-only point inventory contract

This phase implements source and a pure decoder, not an actual acquisition.
Never execute the ELF on the host. No guest runner or new capture is included.
Legacy PR34 C/parser/captures and PR54 synthetic contract stay unchanged;
legacy M1 remains OPEN. A new implementation cannot retroactively repair v1 bytes.

## Wire and source roles

`guest-data-fd-denial-observed-v2` uses the exact flat rows documented in
`docs/evidence/deny_fd_v2_schema.json` and the approved combined spec.
The pure API is `wire.decode(raw)->Capture`,
`validation.check_inventory(capture)->Decision` and
`validation.canonical_digest(capture)->str` in `tests/deny_fd_v2/`.

The supported point is PRE_EXEC_INVENTORY only. Operation FD is null because
there is no syscall being attributed. Configured subject is policy context,
not the causal FD. Every observed descriptor has its own exact same-point FD
row; sorted CAUSE rows reference those original sequence identities.
`extras=observed-expected` is a denial only when missing is empty and extras
nonempty. Missing/mixed sets have explicit unsupported RESULT values. A complete
empty inventory is not unknown. FD0 is valid. All unknown generations and drops
remain null; local IDs/timestamps establish no kernel lifetime or losslessness.

Exactly one LF/CRLF framed DFD2 window is accepted, with strict contiguous
UInt64 sequences and increasing observation times, Int32 nonnegative FDs,
bounded scalar fields, explicit null and no Bool/Float/nonfinite coercion.
The resource limits are1024events/64FDs/4096linebytes/1MiBserial,not scientific
admission thresholds. Old HFD/v1 and mixed protocols are rejected,not adapted.

The OBSERVED_UNTRUSTED header is a claim in untrusted bytes,not acquisition proof.
Synthetic fixtures remain synthetic even when the header has that spelling.
WIRE_DIAGNOSTIC_CONSISTENT is always BLOCKED; all nine operational permissions
are false. No PR54 evaluator/receipt adapter or application/estimator bridge exists.
Digests identify content,not authenticity,safety approval or authorization.

## Fixed C source — not executed in this phase

The guest-only C source has six fixed installation profiles,one forked root,
an empty initial barrier and a final stopped inventory barrier. Sorted entries
are re-witnessed with fstatat(AT_SYMLINK_NOFOLLOW),never by opening/reading an
unexpected target FD. Every FD's actual emitted seq/time is retained before
SNAP and the actual set-difference predicate; case labels do not choose denial.
The final stopped target is never resumed,including NO_DENIAL. Normal captures
require actual SIGKILL/reap before END. Clock/logging/observation/cleanup errors
must leave failure/incomplete evidence,not repaired zeros or a success frame.

These are source-level intentions verified only by compilation/static review
here. Ptrace/barrier/clock/cleanup behavior has NOT been exercised in a guest.
Point snapshots do not prove continuous inventory,whole-input closure or kernel
linearization. The fixed scope/kernel/root guard is not permission to host-run.
No read/exec/READY stage or transport qualification is implemented by this probe.

## Compile-only provenance

`build.describe_sources(M)` reads a closed six-file raw Git source set.
After source commit M,the source manifest is recorded separately; it excludes
itself,ELF and final capture digests. `build.compile_fixed_probe(destination)`
requires that fixed manifest and byte-identical working sources. It creates a
new owned directory outside checkout,copies the pinned C bytes there,and invokes
only `/usr/bin/cc --version` and a fixed static compiler argument vector.
It checks copied input afterward and inspects the ELF64/x86_64/static headers;
it never launches that ELF. Toolchain/header/library input closure is unqualified.

The pre-build manifest digest and M are compiler definitions; ELF hash and
compiler command/version are post-build metadata. There is no self-hash cycle.
Output/source/permission errors do not fall back to HEAD,another compiler,an
unbound binary or execution. Actual capture/image/VM binding is a separate task.

## History and authority

P3 freezes the one approved old loader hook after base75fd435. New helper pins
P3 outside that postimage. Original P/P2 checks and all prior tests/guards remain.
Historical P2 cohorts get no new paths; missing Git objects are not negative
ancestry. Current cohorts require exact P3,39preserved paths and one frozen hook
in HEAD/index/worktree,with actual Git-clean CRLF equivalence only.
The exact18new paths are not a directory wildcard or execution authority.

Retained:OBSERVED_V2_CAPTURE_UNAVAILABLE,LEGACY_PR34_M1_OPEN,
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED,WATCHDOG_EXECUTION_MODEL_UNRESOLVED,
EXTERNAL_EXECUTOR_UNQUALIFIED,APPLICATION_NOT_AUTHORIZED and all inherited
runtime/vehicle/empirical blockers. PR54's fixed PRODUCER_NOT_IMPLEMENTED rejection
remains its own historical API boundary and is not bypassed by this decoder.
