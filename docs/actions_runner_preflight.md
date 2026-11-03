# Read-only Actions runner preflight: local registration

This phase adds the prepared manual workflow locally. It does not publish it,
register it with GitHub's server,dispatch it,or qualify a runner. The display name
retains `(unregistered draft)` because the exact prepared bytes are preserved.
GitHub default-branch availability,policy,permissions,billing and server validation
are still unverified. A successful future job means only that the collector ran.

## Frozen inputs and successor scope

Base and synthetic phase endpoint:
`33d358fdac148fccc7f02c19e24bb35c4b09e417`.

The original->H1->design range checks still run. The existing design->synthetic
range now ends at that literal checkpoint and checks the complete old inventory.
A separate successor guard admits only the six paths listed in
`docs/evidence/audit_compatibility/actions-runner-preflight-v1/registration.json`
and modifications to the old guard consumer and `.gitattributes`. Its literal
allowlist is in code;editing the current manifest cannot authorize another path.
The original `_phase_changes` and all old nonconsumer functions remain unchanged.
New tests reject unknown paths/statuses/aliases,changed frozen-range inputs,and
untracked extras through the actual consumer. No old threshold or test is removed.

Prepared fixed manifest content identity:
`2b7ffd5d32014d74a24e442f1b14b6a81cd73b1a8c66b7deb069d80064fa7f60`.

- `tools/actions_runner_preflight.py` SHA-256:
  `3b3b99e4fb1dab67b2972c06cc432ed80f6b38c3f48c3aa69a4d13517750429e`.
- `.github/workflows/runner-preflight.yml` SHA-256:
  `40781c65ecb75467cdcd1204902e72869249ad018c7c4bc51e11996830572b1d`.

The collector and inline executable body are adopted byte-for-byte. The YAML
container removes only one final empty line flagged by `git diff --check`;
adding that LF reconstructs the prepared workflow hash
`36bb270a74d831637c44f6cb9eb73e431366af127c2de61461797c58be0e668f`,which is
independently checked. No trigger,permission,job,or command changes. Attribute additions force LF for
these two paths;all earlier attribute rules are retained. These hashes identify
content,not authenticity,safety,authorization,or an exact runtime fingerprint.
The preparation's old C0/I1/M0 review and RED->GREEN I1 fix are not represented as
a final clean review. This registration has its own exact-head review evidence.

## Closed workflow and read-only collector

Manual `workflow_dispatch` only,Ubuntu24.04,two-minute job timeout,workflow/job
permissions `{}`,one bash/Python step. No actions,checkout,installation,inputs,
services,network commands,upload,credentials,sudo,namespace/control mutation,
H/O/D,new synthetic workload,vehicle,Params,controller,schema or application call.
The inline source is exactly the standalone collector;no repository code is
checked out or imported by the observation job. Existing CI is unchanged.

The collector reads only bounded host/Python/UID metadata,selected process security
fields,three old S-v1 tool hashes,native API presence,and conservatively mapped
cgroup2 values. It confirms its own PID and detects before/after membership/mount
disagreement,but never claims atomicity or private/delegated resource limits.
Final-component nofollow/nonblocking regular-file reads are not general ancestor
symlink or hostile-kernel containment. W_OK is not a write/delegation trial.

Unknown values remain `None`;zero and empty valid controller lists are preserved.
CPU/scalar/type/controller fields use distinct grammars/known-token allowlists.
Malformed printable text and unknown future controller tokens are unavailable,
not echoed. No numeric safety thresholds or new execution profile are invented.
GitHub environment fields are a five-key validated allowlist and remain
`UNVERIFIED_CALLER_METADATA`. No actor,hostname,full environment,secrets,or raw
cgroup/mount paths are emitted. Output is at most32KiB of single-line JSON.

All output remains `BLOCKED`/`NOT_EVALUATED`,atomic false,aggregate boundary
unqualified,H not executed,and all nine permissions false. Presence/hash equality,
synthetic tests,source metadata,or job success cannot grant execution/application
authority. Historical replay,source atomicity,ENTRY/stack/CI adoption,and all
existing project/vehicle/application/estimator blockers remain.

## Portable regression contract

All93prepared test cases are retained with portable source locations and a closed
stdlib canonical-template consumer instead of a dependency on a particular system
Python/PyYAML. The actual extracted Python body executes through `sys.executable`
on every host. Linux-only descriptor/hash/metadata/bash observations gate before
native setup and record `UNAVAILABLE_NOT_KERNEL_PASS`,not skip/xfail or kernel
success. Local unsupported-host simulations do not establish actual Windows or
GitHub compatibility. Optional local YAML parsing is validation evidence only,
not a new package/CI dependency. Product and existing CI configuration are unchanged.

Run `python -m pytest -q` for all regressions. No registered test is removed and
the collector coverage target stays statement>=98%/branch>=95%,zero exclusions.
Prior full regressions include existing bounded S-v1 observations;they are not H.

## Remaining next task

Perform a read-only publication/Actions-access preflight for the local exact head:
compare remote base/branch state and available workflow permission before any
separate publish/merge/dispatch. No access,account cost,policy exception,or remote
write is assumed. GitHub log retention is not independent custody;future Hugging
Face archival/receipts remain a separate action. Do not promote local observations
to GitHub evidence or automatically start H when a workflow is accepted.
