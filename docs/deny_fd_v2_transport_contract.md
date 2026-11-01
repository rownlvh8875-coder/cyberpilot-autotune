# Dedicated DENY-FD v2 transport contract

Source-only successor of27cfdee;P5f45e345281e1b378276db912556f3453218a9c99
pins76preserved files and2explicit routingpostimages. All old P4 records/M2
sources/failed raw remain unchanged. Exact2modified+20newpath scope only.

Kernel/diagnostics belong to ttyS0;new fixed telemetry uses ttyS1, raw mode and
no console fallback. New init refuses missing devices/stty/setup failure before
DFD2_EXEC. Probe byte identity and case profiles remain unchanged. New image
build produces data only;it does not boot or qualify a guest. Kernel config8250
support is not evidence ttyS1 has actually enumerated or passed device setup.

StreamEvidence preserves separate immutable raw bytes/completeness/errors.
Unknown is never defaulted to zero/false. Sum of retained stream bytes<=1048576.
TransportProcessResult distinguishes actualprocess exit from collector errors;
structural construction itself does NOT admit a capture. Explicit stream roles
must remain separate in future receipts;old acquisition-v1 is not dual-stream-v1.

Fixed asset preflight verifies the new transport semantic manifest and exact
kernel config hash,then reuses old complete source/probe/VM verification read-only.
No downloads/rebuild/fallback/caller profile. Missing or drifted data fails closed.
No import-time file access/spawn. No new installed-product/estimator/application
adapter. Ninepermissionsfalse and every inherited blocker remain. Hashes identify
content only,not authenticity,qualification,approved values or authority.

## Source collector and evidence envelope

The dualFIFO collector and new dual-acquisition-v1 serialization are implemented
as test-only source. Fixed QEMU argv adds a second ISA serial index1/pipe chardev;
the first serial/stdout+stderr stays console. Endpoint paths reject comma/control
characters;newFIFO paths are exclusively created0600 with no symlink fallback,
open-handle/path identity and non-inheritable host descriptors. FIFO anchors do
not imply EOF or successful connection. An exited owned leader plus a bounded
drain determines byte completeness;early EOF before exit never finishes capture.

Each ready stream gets at most65536bytes per iteration. Aggregate retained data
is at most1048576bytes,180sdeadline and2sTERM grace;overflow/timeout/read/selector/
close/cleanup/persistence errors invalidate acquisition and retain actual prefixes.
Supported first close interruption gets one idempotent close retry. Interrupted
cleanup gets one immediately escalated ownership-checked attempt,no second TERM
grace. Reaped or unowned leaders never select an alternate PID. Universal escaped
session/descendant closure or arbitrary repeated-interruption recovery is unqualified.

The record binds distinct telemetry/console digests,size,complete/error fields,
actualprocess exit/termination/collector error,source/probe/build-cohort/VM/kernel/
kernelconfig/transportprofile/init/image identities,exactargv and UInt64hostclock.
Unknown clock leaves an absent record rather than a fabricated timestamp. Current
frozen record and earlier completed records remain available on supported storage
errors;exclusive writes may leave partial files. Each raw file write is attempted
independently even when the record/end clock is unavailable. A diagnostic envelope
then records null record/digest if unavailable and explicit raw write outcomes;
one failed write does not stop the other raw stream or metadata attempt.
No crash-durability guarantee.
Failure_reason remains diagnostic envelope text outside the record contentdigest.

Only telemetry enters the unchanged strict v2 decoder and oldsource/case/policy/
inventory binding check. Console noise is not filtered into/out of telemetry;
noise IN telemetry still rejects. Valid telemetry never erases another stream's
or collector's error. No input is relabelled an original accepted capture.

Default CLI/import performs no preparation/spawn. CLI always exits2/BLOCKED,
including a future internally consistent RECORDED_UNTRUSTED result. Nineflags
stayfalse;diagnostic opt-in is not an authority grant. FAILED CLI results include
both bounded raw prefixes losslessly as explicitly labelled base64, including
when every file write fails. This is a diagnostic recovery envelope,not telemetry
repair or an accepted observation. Encoding expands at most the aggregate1MiB
raw data by ordinary base64 overhead;the raw acquisition cap is unchanged.
If all file and CLI output destinations fail,universal recovery is not promised.
No actual QEMU/probe/guest
execution or runtime qualification is authorized by this source document.
