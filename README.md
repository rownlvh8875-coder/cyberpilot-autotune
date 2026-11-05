> This README describes the preserved direct-child profile at9545d54.
> Internal-D successor: [design](INTERNAL_D_DESIGN.md), [final report](LOCAL_INTERNAL_D_FINAL_REPORT.md).
> Neither profile is a qualified product provider.

# Native E local research prototype

Independent Linux lab, not a CyberPilot provider and not product integration.
Product reference: cyberpilot-autotune 4b77b31dd23010f2d2b394466d88b04a4a2720e2.
The frozen product checkout and all its guards stay unchanged.

## Implemented
- run_fixed() has no caller-selectable command, path, PID, FD, unit, payload or receipt.
- Linux C E creates a sealed constant memfd and socketpair, then clone3(CLONE_PIDFD)
  creates the one compiled-in worker and its original pidfd atomically.
- Worker blocks before synthetic work. BIND/OWNED/RUN/DONE/COMPLETE are execution
  stages, not callbacks or qualification records. The controller must half-close
  after exactly one RUN. Bad contexts, extra frames, ancillary FDs or EOF fail closed.
- Fixed worker receives only its own local socket, sealed synthetic memfd and null
  standard streams; no directory FD, inherited environment credentials or arbitrary payload.
- On control loss E signals only its retained direct-child pidfd and attempts one
  bounded wait. Unknown close/wait stays unknown without numeric PID/name recovery.
- Frozen passive Observation cannot stop or recover anything; serializing it grants
  nothing. Live helper handles reject pickle/copy, retain original OFD anchors, compare them with
  same-process kcmp(KCMP_FILE), and retain terminal uncertainty. If comparison is unavailable,
  close is UNKNOWN and no metadata-only fallback is allowed.
- Optional run_user_lab() factory creates a new external unit and blocks worker launch
  until manager properties and self cgroup kernel limits are checked.

## Explicit limits
NO internal D implementation, cgroup creation custody, aggregate descendant custody,
admission fence, namespace containment, readonly mount, external-writer/async drain,
host crash recovery, native provider binding or actual H execution.
A systemd-created lab service is NOT an E-created original D.
Same-UID hostile code, arbitrary in-process Python mutation, close/reuse races and
hostile FD-table alias/generation mutation are not a security boundary here.
Directory fixtures have checked metadata but mkdir/open and lstat/rmdir are not an
atomic directory custody protocol. Handle-loss tests retain private residues.
No constructor, digest, numeric descriptor or path can reconstruct live authority.
The compiler, kernel, source tree and controller are trusted research inputs,
not qualified or independently authenticated components.

## Reproduce in a new Ubuntu-24.04 workspace
Use Python 3.12, a dedicated venv and project [dev] dependencies. No sudo/global installs.
On this notebook ensurepip is unavailable; the dedicated venv was made with
--without-pip and bootstrapped with an existing bundled pure-Python pip copy.
Build/test commands:
```sh
.venv/bin/python -m native_e_lab.build_native
.venv/bin/python -m pytest -q --cov=native_e_lab --cov-branch --cov-report=term-missing
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src/native_e_lab
.venv/bin/python -m build --no-isolation
.venv/bin/python -I -B -c 'from native_e_lab.runner import run_fixed; print(run_fixed())'
```
The last command runs only the fixed synthetic worker. The compiler emits a local
binary/hash sidecar, both excluded from source Git. The wheel contains C source;
build_native must be run in its own writable venv before native experiments.

A separately explicit lab call is:
```sh
.venv/bin/python -I -B -c 'from native_e_lab.lab import run_user_lab; print(run_user_lab())'
```
It creates ONE fresh external unit, with 30s runtime / 5s stop / 128MiB memory /
zero swap / 8 tasks / 25% CPU. It never starts/stops/restarts existing services.
The original systemd-run job is retained through completion; no stop-by-name,
reattachment from old receipts or full WSL shutdown is provided.

All 14 project admission/qualification flags stay false, provider_registration
is UNBOUND, and the old 16 evidences remain UNAVAILABLE.
