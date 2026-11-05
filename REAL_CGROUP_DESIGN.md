# Fixed real-cgroup2 user-unit lab adapter

Base ed8b68a993ea90e3f55b4931e3393bab464fee42.
Research only. Provider UNBOUND /16qualificationUNAVAILABLE /all14flagsfalse.
Existing111 source/test/report files unchanged; PLAN/PROGRESS append-only.

## Scope and ownership

The only actual OS activation is a fresh user-level transient lab service.
Existing user manager/root slice must already be active with cpu memory pids enabled.
Fixed Slice=-.slice is the user-manager root, NOT the host root. It avoids enabling cpu on app.slice.
No existing service start/restart/stop, controller configuration, root/account, mount/namespace or vehicle work.
Bounds: RuntimeMax30s,TimeoutStop5s,MemoryMax128M,Swap0,Tasks8,CPU25%,NNPyes,Delegateyes,Restartno.

External P belongs to the systemd-created new unit. F opens the current attempt's P once and retains OFD refs.
P is not an E-created internal D or creation-time original F custody claim.
F never unlinks P. E alone creates D from its received live P and owns original W pidfd.
The private inner M remains synthetic; user systemd creates only the outer lab service.
Credential mutation remains no-forward simulation. Actual W UID/capability transition is not certified.
FS/CLONE_INTO_CGROUP/cgroup.kill are unwrapped in the positive lab, unlike prior virtual controller tests.

## Files and gates

- factory.c: fixed F successor using old private sd-bus/NPG1/lifetime helpers, releases P refs.
- scope.c: old pinned self-membership/factory-scope/open-parent guards; never old launcher.
- normal.c: fixed normal M and credential-shim selectors; no runtime fault API.
- build.py: fixed private kit/source snapshot/strict compile/hash-bound original ELF FD.
- gate.py: factory GO token, absolute8s framing deadline and explicit EOF, kernel limits/NNP/scope/source checks.
- lab.py: no-arg public fixed lab, fresh random unit/token, loaded properties before GO and original job completion.
- tests/test_real_cgroup.py: no unit activation. Controller fakes, native default rejection, source/FD/EOF/failure tests.

The gate execs the original verified F file descriptor in the SAME PID instead of spawning another F.
Directory descriptors are closed first; the CLOEXEC executable FD is consumed by exec.
No arbitrary caller-selected path/PID/FD/unit/command/receipt recovery API exists.
Private kit paths and unit identifiers are internal current-attempt data, not permission records.

Source inputs are captured once into a fresh private snapshot, actually compiled from that snapshot,
and both original and snapshot bytes checked after compilation. Pins describe those exact captured bytes.
Gate checks current source and fixed asset names/hashes, private ownership/modes, regular files.
FIFO/file-type refusal is nonblocking. Hashes do not authenticate protected root code or loader origin.
The adjacent fixed worker remains a trusted same-UID private-build assumption, not hostile-writer attestation.
No F1/admission fence or protected loader/readonly-mount/namespace guarantee is claimed.

After communicate starts, it exclusively owns pipe closure; uncertain job and pipes are retained.
Before that boundary, our close ownership is consumed before one attempt. Unknown close is not retried.
No unit-name stop/kill/recovery. The original fresh job and preconfigured runtime bounds govern this lab.
Native M/E/W original waits, one-shot D stop, exact SIGKILL and D removal are unchanged from the pinned component.
SDK internal close remains UNAVAILABLE even after native success.

## Serial experiments and continuation

Only after pure tests/review/source-bound runtime commit:
1. Fresh positive unit, verified manager and kernel bounds before native entry.
2. If completed/inactive and operating metadata preserved, a NEW serial private-kit drift-negative unit.
   Append fixed non-sensitive bytes only to that new kit's worker. Gate must reject before F/D/W.
Any unknown/active prior lab blocks further OS activation. No reattachment or retry of old residue.
Experiment scripts also check limited active lab-prefix state and existing controller/manager identity.
All raw unit/PID/path records remain private; public report/evidence uses sanitized results/hashes.

Success is real kernel cgroup2 placement/kill in a trusted fixed lab, not provider/runtime qualification.
