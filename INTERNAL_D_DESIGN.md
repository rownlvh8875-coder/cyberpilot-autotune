# Internal D trusted-lab successor
Goal: E creates a NEW child cgroup D inside ONE newly factory-created delegated user service;
clone3(CLONE_INTO_CGROUP|CLONE_PIDFD) births only the compiled fixed worker in D. E remains outside D.
E stops through original D fd once, reaps original pidfd once, verifies populated0 and removes its new D.
The systemd-created service is external lab scope, never D. Existing cgroups/controllers/processes untouched.

Public API: run_domain_lab() (no arguments). Gate validates same six resource limits and Delegate=yes;
native preflight verifies current namespace cgroup2 mount, fresh factory service shape, owner UID, parent FD.
Only new D control writes permitted. Parent/controller settings never written, no cgroup.procs moves.
No arbitrary command/path/PID/FD/unit/receipt import/recovery API; old run_fixed/run_user_lab remain supported.
E retains parent and D fds plus original clone pidfd; private random D name is bookkeeping, not stop authority.
Before cgroup.kill: current D members exactly the held child; E's own cgroup differs from D.
Failure -> no kill of unknown membership; retained pidfd can stop ONLY original fixed child.
Unknown write/wait/close/removal stays UNKNOWN, no retry or reattachment. No cleanup by old path.

mkdirat -> openat has no atomic Linux mkdir-return-fd primitive. In this trusted single-owner lab,
no worker or second E thread runs in that acquisition gap; original inode/OFD/name checks precede admission.
This establishes observed creation/admission/stop sequence, NOT hostile same-UID atomic custody/admission fencing.
Bootstrap trampoline must close inherited directory fds before worker entry; verify its FD set before work.
No namespace containment, readonly mount, external writer/async drain or native qualification claims.
All14 flags false, UNBOUND,16 UNAVAILABLE retained. No product/vehicle/remote changes.

## Post-review execution-image refinement
Native E birth trampoline now execveat's a fixed pinned worker ELF by retained executable fd.
CLOSE_RANGE_CLOEXEC marks5..max; only0..4 are exported, and kernel exec closes directory fds
before worker image entry. Parent verifies the expected executable inode and FD set before RUN.
The temporary pre-exec trampoline is still trusted E code; no separate namespace sandbox claim.
This refinement is author verified after the independent3f72 review, not independentlyC0/I0.
