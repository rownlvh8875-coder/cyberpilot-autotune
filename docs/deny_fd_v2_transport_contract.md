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

Implementation checkpoint:assets/types/image present;dualFIFO collection and
new acquisition serialization/admission are NOT yet implemented at this checkpoint.
Default CLI/no-spawn must be preserved when those interfaces are added. No actual
QEMU/probe/guest execution is authorized by this source implementation document.
