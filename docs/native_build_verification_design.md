# Offline full-native-build verification design

## Decision and authorization boundary

This task designs verification; it does not execute it. Continue from CyberPilot
PR21 `efdec237947bb47eebdbecebb2680114f085c3eb`, preserving its registration fix
and every native patch byte. No new runner, Dockerfile, dependency install, native
checkout, SCons invocation (including help/dry-run), image pull/container, service,
device, Params/SubMaster, fork publication, merge or deployment is authorized by
this document. Future execution needs an explicitly approved stage below.

The selected future profile is `PC_X86_64_ROOT_DEFAULT`: Ubuntu24.04 linux/amd64,
Python3.12 (source range `>=3.12.3,<3.13`), all locked extras, default root
`SConstruct`, extras enabled, initially two build jobs. This is a desktop build
profile, not the user's vehicle/device fingerprint. The exact image, Python patch,
uv, system packages and LLVM artifacts are deliberately **unqualified inputs**
until acquired and sealed. Resource sufficiency is not established.

Native identity is fixed:

| Input | Exact identity |
|---|---|
| R | `c2130730239bcdb4cbde9361ab90c8d99aa4ff55` |
| R root tree | `ffb213d9fdc0f9618264822bd2a4e26263abfe74` |
| unchanged patch SHA-256 | `8aa8b63b16ad2050280b3d5e08bc8712111c29014338ef85020aa934787ee8ac` |
| patched complete tree | `6185197d6f334f745a9c082519013b8fe0376f65` |
| offline synthetic recipe commit | `9957868acc7459f515f1b79e9315cf93a878d933` |
| comparative C | `f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3` |

The synthetic commit is not published/fetchable; reconstruct it using the existing
registration record, not `git fetch` of that SHA. Full tree identity is not full
blob availability: the warmed partial reference is not a build checkout.

On 2026-10-29, the designated `ajouatom/openpilot:carrot-wip` re-query still equals
C: `f5e4f8b8a1589e908811c751ea0a2ab2218bd4a3`. No movement or promotion. The user
fork's same-named branch points to a different ancestor; comparing two repositories'
branches does not establish a rewind. Bind repository **and** branch in every
observation; an initial wrong-repository interpretation was corrected before
publication. See [source evidence](evidence/native_build_verification_sources.json).

## Why root-default, not a smaller smoke build

R's native-cpu workflow uses Cython3.2.9 and
`scons -f tools/native_cpu/SConstruct -j2`: radar-motion, CAN and nativeUI only.
R's project lock instead selects Cython3.3.0. Neither that subset nor the existing
192 schema/body/registration tests proves a full native build. The tests workflow
declares Ubuntu24.04 setup plus root `scons`; a declaration is not an observed
successful exact-R run.

Root default enables extras when `.gitattributes` exists (it does at R). Preserve
that file and do not use `--minimal`. The graph includes cereal C++ generation,
common/msgq/DBC/rednose, debug Panda/jungle firmware, loggerd, pandad, MPC,
locationd, model compilation, UI/fonts/nativeUI, carrot/navigation/CAN and host
replay/cabana/jotpluggler. TICI-only camerad and device backends are not in this
profile. Do not skip a failed target and label the result full.

All extras match the source setup's dependency selection, including tools/testing
needed for imgui/bootstrap-icons/Catch2 and otherwise unnecessary docs/dev/
metadrive inputs. Do not silently slim the closure after failures. Building host
tools or firmware does not authorize launching/flashing them.

## Four gates, separately authorized

| Gate | Deliverable and acceptance | Stop condition |
|---|---|---|
| A: acquire/audit | complete immutable source + dependency/toolchain/asset inventory; static configuration/action import and IO audit | missing bytes/hash, mutable ref, forbidden side effect or unavailable artifact |
| B: seal | digest-addressed Ubuntu image and offline input closure, reproducible recipe and resource budget | unpinned OS/Python/uv/LLVM/toolchain, unresolved writable paths/imports, insufficient space |
| C: build | cold R B1/B2 and patched P1/P2 root-default builds in identical offline sandboxes | gate mismatch, denied network/Params/device/service action, target/compile/link failure |
| D: assess | generated C++ schema checks, target/artifact comparison and honest qualification report | missing full graph, unreviewed variance, safety/runtime claims inferred from compile success |

A/B preparation may need network and dependency package build hooks. Audit hooks
before executing them, only in an approved disposable preparation sandbox with
session proxy/CA and TLS/signature verification intact. No host setup wrapper,
uv self-update, unlocked dependency resolution or secret/SSH-agent forwarding.
Do not pass proxy credentials into final image layers/evidence. BuildKit CA trust
uses secret mounts; it does not disable TLS. Acquisition is not performed here.

Offline C/D have network disabled, no credentials, Docker socket, host home,
`/data`, device, GPU, display/audio or X11 mounts; no privileged/host-network mode.
Use a non-root image user and no `/TICI` or `/AGNOS` markers. Inputs are read-only;
only task-specific native build trees, scratch/cache and artifact output are
writable. Preserve image-defined HOME; never redefine HOME/home/CODEX_HOME.
Allow only OS pseudo-devices needed by the sandbox, not vehicle/device access.

## Configuration is execution

Panda's SConscript unconditionally writes board/obj version/certificate headers
while configuring. Modeld's SConscript immediately runs tinygrad device discovery
and later compiles driving/monitoring model artifacts. Thus `scons -h`/`-n` is not
a read-only preflight. No such command was run this task.

Before gate C, statically audit the **transitive** SCons/import/build-action graph,
including hardware constructors, model helpers/catalog, code generators and
dependency build hooks. Known catalog import reads source catalog and optional
selection/boot metadata; use an empty isolated image user state, never host state.
This limited reading is not proof of the entire graph's purity. If the unchanged
graph requires real Params, SubMaster, runtime service, device access or delivery
downloads, stop and report a scope blocker; do not mock/patch it to force a pass.

CPU-only discovery must be observed, not assumed from lack of GPU mounts. R selects
CPU:LLVM on Linux when CUDA/QCOM are absent; record detected devices and LLVM
library/compiler identity plus CPU feature selection. Unset inherited
BUILD_USB_GPU_MODEL/BIG_INTO_SMALL and custom model selectors; do not set fake
hardware markers or silently force a different backend. No optional eGPU delivery,
remote model manifest fetch, model daemon or vehicle inference is permitted.

Panda requires its locked ARM compiler and default debug signing fixtures even
for this host build. Require RELEASE/CERT/DEBUG absent from inherited environment;
never use a production certificate, disclose signing material or flash firmware.
The committed debug fixture's source pin is sufficient; don't dump its contents.

## Repeatability and outputs

Each of B1/B2/P1/P2 starts from a complete pristine source tree and a separate empty
SCons/tinygrad/compiler cache, without a prior native .venv or generated artifacts.
Use the same in-container path `/work/native` and identical sealed dependencies,
environment, umask, locale, UTC timezone, image and CPU exposure. Record R's commit
epoch `1793169535` as SOURCE_DATE_EPOCH where honored, not a claim all generators
honor it. Do not substitute CyberPilot's environment for the native lock.

Assign task-specific SCONS_CACHE_DIR and scratch paths. Clear inherited
SCONS_CACHE_LOCK_FD and build/compiler overrides; supply only the sealed allowlist
of environment keys. No global cache, `scons -c`, recursive cleanup or git reset/
clean of shared checkouts. R makes its cache a Clean target and locks its sibling
lock file; isolation avoids destroying another task's cache.

After A/B approval and receipt validation, gate C's root build command is
`.venv/bin/scons -j2 --verbose` from `/work/native`. It is a **future command**,
not executed evidence. First install the native environment from the sealed
closure with pinned uv using `uv sync --locked --offline --all-extras`; no lock
rewrite, re-resolution, fallback index or network bootstrap. Validate the exact
uv CLI and cached PEP517/VCS artifacts during gate B. A cache miss is a failure,
not permission to go online. A package hook's network attempt is likewise a stop.

Save command exit status, complete logs, source/config/dependency receipts,
compile_commands.json, default-target inventory, generated cereal headers/sources,
resolved library paths/versions, artifact SHA-256/size inventory and denied-access
events. Artifacts may include executables and debug firmware: quarantine them as
build evidence; no launch, install, release, publish or flash.

Distinguish COMPILE_PASS from REPEATABILITY_PASS. Compare B1↔B2 and P1↔P2 raw
artifact bytes, including models/firmware; explain every variance rather than
discarding nondeterministic bytes. B↔P differences may propagate through cereal
headers to many link consumers, so do not demand or assert blanket binary equality.
A source-tree diff still must contain exactly the existing six modifications and
one addition. Neither repeatability nor compilation approves control behavior.

For D, inspect actual generated C++ new receipt definitions/ordinals/types and
compile a tiny standalone synthetic schema-only round trip against generated
cereal/KJ/Cap'n Proto, not common/PID/controllers/services. Verify explicit
availability vs zero, Float64 raw values and old/new unknown-field compatibility.
Use only deterministic synthetic values; never execute built controller, model,
replay, hardware, transport or firmware entry points, nor blanket native pytest.
The probe is future work, not implemented by this planning task.

## Current environment: observations, not requirements satisfied

This managed host is Debian13 x86_64, not the source setup's Ubuntu24.04 target.
Python3.12.14 and uv0.12.23 observed here are not a sealed native toolchain.
Docker28.4.0 local daemon responds; storage driver vfs, five visible CPUs but
cgroup quota four CPUs, memory32GiB. Observed free workspace30GiB/tmp16GiB is a
point-in-time measurement, not a full-build capacity claim. Two initial jobs are
a conservative planning choice, not validated peak memory/time/space.

Budget the image/layers (vfs duplicates), complete source and model payloads,
dependency build caches/venvs, four cold build outputs and logs **before** C.
One isolated sandbox at a time may reduce peak disk; retain immutable evidence
before retiring a sandbox. No image was pulled and no container was started.

## Authority retained

This plan changes only new documentation/evidence. PR8/9/16/17/18/19/20/21, main,
native patch, installed package, H6/H7 policy, tests and CI are unchanged.
q_observed remains null, consumed-source completeness unresolved, the instrumented
revision/schema pair still rejected by H7. All candidate/application/runtime/owner
proposal permissions remain false. A full-host build, even if later successful,
does not register/qualify that source, implement independent q, qualify timing,
device compatibility, empirical estimation or application authority.

See [dependency inventory](native_build_dependency_inventory.md) and the
[future execution plan](superpowers/plans/2026-10-29-offline-native-build-verification.md).
