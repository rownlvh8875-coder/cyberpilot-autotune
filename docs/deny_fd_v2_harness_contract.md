# DENY-FD v2 fixed isolated harness

Local implementation scope: a separate test-only harness, not actual acquisition.
The exact design and22-path implementation plan live under docs/superpowers/.
Fixed M2 producer bytes and all v1 sources/captures remain unchanged. P4 routes
only the new exact scope; the original19-path node replays original base source.

Default CLI/import/test/build must never launch QEMU or the probe. A future
explicit guest diagnostic has six fixed cases, pinned VM/probe/source/image
identities, no caller command/payload/VM override and bounded retained raw output.
All decisions remain BLOCKED and nine operational permissions remain false.
No actual guest/capture or runtime/watchdog/application qualification is claimed.

## APIs and fixed content

`assets.preflight()->AssetBundle` verifies the closed assets profile, original
M2 source/compile record and complete cached5502-entry VM cohort. It retains
verified probe/busybox bytes. Missing or changed inputs fail without download,
rebuild, alternate binary or version fallback. The relocated compile record
keeps its original command; relocation does not establish reproducibility.

`image.build_image(bundle,case)->bytes` builds an in-memory minimal deterministic
newc/gzip archive for DFD01–DFD06. It contains only static busybox/probe, five
bootstrap directories, console/null nodes, fixed v2 scope and init. Its output
is data, not an execution capability. No host extraction or guest execution.

`capture.validate_capture(raw,case,bundle)->Capture` reuses only the unchanged
v2 decoder and point-inventory checker. It binds BEGIN source/manifest/case and
the requested POLICY/EXPECT. Actual FD/CAUSE/outcome still come from raw rows,
not case labels. A consistent result remains untrusted and BLOCKED.

`runner.capture_cases(cases,destination,run_prepared_guest=False)` rejects before
preparation by default. Future opt-in requires unique fixed cases, a new owned
absolute output outside checkout, fixed Linux waitid/group support and a fresh
preflight before each launch. The only launch argv selects pinned loader/QEMU/
kernel/BIOS and a newly prepared image; no caller payload, command or VM options.
The image's regular-file binding and bytes are checked before launch. This is
ordinary drift detection, NOT execution-time input sealing or hostile-host trust.

`host_main.main` always exits2/BLOCKED, including a future diagnostic success.
Default/missing selections return NOT_STARTED with no preparation or spawn.
There is no auto-start via imports, build, pytest, CI or an environment variable.
The explicit flag is diagnostic intent, never AuthorizationGrant or application
authority. This work does not authorize actually invoking that future path.

## Receipt and error meaning

Frozen `AcquisitionRecord` separates raw bytes, explicit raw completeness,
nullable process exit code, termination reason, source/build/VM/kernel/init/image
identities, exact argv, host attempt identity and UInt64 monotonic host times.
Unknown exit is None, not0/false; bool is not an integer value. Guest event time
uses a different clock and is never subtracted from host time here.

Its canonical content digest covers metadata, raw SHA256/size, fixed false
permissions and schema `deny-fd-v2-acquisition-v1`. It does not authenticate
acquisition. The record.json envelope's failure_reason is separate diagnostic
text outside that record digest. No part is QualifiedEvidence or an authority.

Future output is one new directory per fixed case: initrd.cpio.gz, serial.bin,
and record.json, all exclusive-created, never an overwrite. Supported timeout,
output-limit, nonzero, collector/close and persistence failure paths preserve
the observed raw prefix and earlier completed records through CaptureFailure.
Persistence failure can leave partial files; the exception retains available
bytes instead of reporting success. No universal crash-durability claim.

Collection is bounded to1MiB and180seconds with a2second termination grace.
The Linux leader remains unreaped using WNOWAIT until the last group signal,
avoiding selection through a reaped/reused PID. Unknown ownership does not
fall back to another PID/group. Group termination is not full descendant/session
closure, continuous FD/OFD proof, qualified watchdog or external executor trust.
Tests with harmless host Python workers do not establish QEMU/C/kernel behavior.

## History and retained blockers

P4=06f959c12b2e2fdf3c9a374ee9787001483fc587,sole parentB. The pinned manifest
contains56preserved images,2explicit routing pre/postimages and20new literal
paths. The helper pins P4 afterward; no self-hash cycle or directory wildcard.
Historical cohorts get no added scope; Git errors/missing objects fail closed.
Only the old19-path architecture node routes to ORIGINAL B source/assertions in
an isolated checkout with its unchanged60second bound; it is not skipped.
The new guard separately requires the actual current22-path delta.

Retain OBSERVED_V2_CAPTURE_UNAVAILABLE,DENY_FD_V2_RUNTIME_PRODUCER_UNEXECUTED,
LEGACY_PR34_M1_OPEN,FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED,
WATCHDOG_EXECUTION_MODEL_UNRESOLVED,EXTERNAL_EXECUTOR_UNQUALIFIED,
APPLICATION_NOT_AUTHORIZED and every prior scientific/vehicle/application blocker.
No runtime producer execution,actual capture,device/vehicle qualification,
candidate generation,owner/application/estimator bridge or legacy-v1 promotion.
