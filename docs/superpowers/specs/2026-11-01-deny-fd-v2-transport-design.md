# Fixed second-serial transport implementation basis

This is source-only planning, not implemented or runtime-qualified transport.
Base27cfdee. Exact22-path proposal is in ../deny-fd-v2-transport-scope.DoxbyO/.
Existing implementation/CI review and failed DFD01 raw remain unchanged.

## Evidence checked this turn

Pinned boot/config-6.12.113+deb13-cloud-amd64 SHA256
3540f9dc8a7e48ef1d2e7b945a87976cf292f736d297cfebe3ac5cdf8571ee1e:
CONFIG_TTY=y,CONFIG_SERIAL_8250=y,CONFIG_SERIAL_8250_CONSOLE=y,
CONFIG_SERIAL_8250_NR_UARTS=32,CONFIG_SERIAL_8250_RUNTIME_UARTS=4,
CONFIG_DEVTMPFS=y. Existing guest log shows8250 fourports but ONLY ttyS0
device observed. Config support does not prove ttyS1 enumeration or raw setup.

Entire M2 probe.c read:collect emits on stdout;bootstrap calls close_range(0,
UINT_MAX,0), stops, then reopens only parent's data primary through /proc and
installs fixed profile descriptors. DFD01 explicitly installs0,3; FD3 in old
capture is intentional profile content, NOT established inherited-console leak.
The probe parent can inherit stdout transport;child inventory must remain exactly
the fixed profile. Parent memfd allocation numbers are not wire ground truth.
Do not change M2 bytes or promote pre-exec inventory to continuous FD/OFD proof.

## Chosen engineering architecture and costs

Kernel and diagnostics:unchanged console=ttyS0, first -serial stdio. Add fixed
second ISA serial index1 connected to -chardev pipe,id=telemetry,path=PREFIX
with new owned PREFIX.in/PREFIX.out FIFOs. No socket or network capability.
Compared to console loglevel quieting,this gives separate streams;cost:two-pipe
supervision and an unexecuted QEMU/backend/device integration boundary.
QEMU named-pipe protocol/CLI acceptance remain future runtime checks, not proven
by kernel config. No alternate backend fallback if setup is unsupported.

Create FIFOs exclusively with0600 under guarded new destination, reject any
existing/link/special-node substitution. Host opens nonblocking read plus temporary
writer anchor on telemetry.out so setup cannot block;stdin channel anchor has no
payload and is retained solely to satisfy backend open semantics. Track anchors
explicitly;close every owned descriptor on all errors. Early readEOF before QEMU
connects is not capture completion. Process exit and final drain define completion;
anchors must not cause waiting forever for EOF. Poll supervisor deadline even
when no bytes arrive. Tests must cover preconnection EOF and held-writer anchors.

New init mounts proc/sys/devtmpfs as before. Require a character /dev/ttyS1 and
successful busybox stty -F /dev/ttyS1 raw -echo -opost; refusal produces no EXEC
marker and no fallback. Open stdout on ttyS1, stdin /dev/null, stderr ttyS0.
No extra persistent guest fd>=3 intentionally held by init/probe command;use
ordinary stdout redirection rather than a separate inherited fd9 transport.
Emit exact framing/probe stdout only there. Preserve probe failure status, no
manufactured EXIT0/DONE success. Device configuration/helper availability remains
fail-closed until actual execution;static shell tests are not runtime proof.

## Supervision and receipt semantics

Immutable StreamEvidence:raw:bytes,complete:bool,error:str|None.
TransportProcessResult:telemetry:StreamEvidence,console:StreamEvidence,
exit_code:int|None,termination:str,error:str|None.
Record includes original source/build/VM/kernel/init/image identities, exactargv,
transport profile+fixed endpoint roles, distinct per-stream digest/size/complete,
host clocks and ninefalse flags. This is a NEW receipt semantic version;never
silently interpret old acquisition-v1 raw as dual-stream-v1. Digest is content
identity only. No application/estimator adapter, authority or successful admission.

Fair selector rotation:each ready stream at most65536 bytes per iteration,
combined retained payload<=1048576, with explicit offending-stream truncation;
no concatenation or filtering. Keep180s monotonic deadline and2s TERM grace,
unreaped ownership checks, bounded cleanup/escalation and supported interruption
context. Drain after process exit to observed no-more-data, bounded by same
deadline;EOF-before-exit does not finish. Handle/persistence errors invalidate
success even when telemetry parses. Unknown remainsNone,never fabricated0.
Original strict decoder consumes telemetry ONLY;console has separate provenance.

## Safety and scope

New descendant only;2routing+20new exactpaths. OldP4 records/postimages/M2 files,
old decoders/harness/product/main/PR8/9/55/56 are preserved. New P5 preregistration
must pin actual76preserved images and two actual routing pre/postimages. No made-up
P5SHA. Runtime guest invocation not part of implementation/gates. No downloads,
compiler,new VM,thread/socket/network,KVM,disk/share,vehicle,Params/controller,
candidate/application/owner/estimator bridge. Ninepermissionsfalse/allblockers kept.
