# Future guest build capture / diagnostic promotion architecture

Design only. No observer, builder, sealing backend, signer, guest run, host policy
or Carrot-native execution is introduced by this branch. Gate A remains BLOCKED;
original B/C/D gates are not started. Static import closure and current hashes
from PR29 do not establish execution-time immutability or build consumption.

## Options

| Capture architecture | Consumed objects / bytes | Lineage and mutation window | Verdict |
| --- | --- | --- | --- |
| Depfile plus post-build hashes | misses loader/link scripts, failed lookups, mmap and non-compiler inputs | post-hoc race; descendants incomplete | insufficient |
| Syscall-presence trace only | requested paths / successful mappings are not returned-byte evidence | exec-loader kernel reads and file-object generations need separate proof | insufficient alone |
| Independent in-guest supervisor plus kernel/file-object observer | actual task/exec/object generations; reads, mappings, bound images and kernel loader paths | observer starts first, independently covers descendants and writer quiescence | preferred future architecture, unimplemented/unqualified |

The observer must be outside the unprivileged fixed harmless build domain, with
complete coverage/failure/drop accounting and independent verification. Its
trust and read-byte/range measurement need separate qualification; the receipt
does not supply them. Include dynamic loader, linker scripts, generated headers,
toolchain/sysroot/config/environment, interpreter exec chains and descendants.
Generated inputs require a future causal DAG extension; v1 refuses to imply full
native build support. A signal/failed/unknown exit cannot promote an output.

Inputs should enter a separately protected immutable namespace only after exact
source/toolchain/recipe/environment/observer bindings are reviewed. Read-only
flags, chmod and matching snapshots alone are not a seal against existing file
descriptors, shared mappings, aliases or privileged writers. The existing1CPU/
768MiB software guest is not automatically a qualified hermetic compiler profile.

## Output lifecycle

Keep outputs quarantined. Independently establish all writer tasks, writable FDs,
aliases and shared mappings quiesced. Copy exact bytes into a **fresh protected
diagnostic namespace**. Seal, independently read back, and bind the final hashes,
phase order, namespace and output generation before diagnostic promotion. Prefer
copy-out over in-place chmod. Produced code is never executed or installed here.
Any mutation/new writer invalidates the assumed chain and requires a new
generation/attempt with new evidence; a digest is not an access-control primitive.

## Gates for an actual implementation (not silently cleared)

1. Qualified executor profile: containment, resource/clock/lineage coverage and
   harmless fixed recipe qualification, independently reviewed evidence.
2. Actual-consumption producer: kernel/file-object identity coverage, returned
   byte hashes and mmap distinction, complete descendants and drops/failure cases.
3. Input-seal backend: immutable namespace/object proof across the build interval,
   not a reference snapshot or caller registration string.
4. Output-promotion backend: writer quiescence, fresh namespace seal and independent
   verification, including adversarial FD/mmap/alias/mutation cases.

The reference-only planner lists these missing/unverified registrations without
probing the environment or generating runnable commands. Automatic continuation
is authorized for ordinary repository work, not fabrication of these witnesses,
host security changes, device/vehicle execution, controller/Params/application,
old PR merges or relaxation of scientific/runtime qualification blockers.
