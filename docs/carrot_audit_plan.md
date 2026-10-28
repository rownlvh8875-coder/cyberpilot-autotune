# Phase 8A source audit plan and gate decision

User authority: source audit, contracts, synthetic evidence and verification only.
Do not implement a mapper while a mandatory signal is unresolved. No actual
cereal adapter, SubMaster connection, Params access, live hook, vehicle install,
reference modification, real logs, persistence or Apply is authorized.

Target base: 09f3f58d9f9f7a59d6f983c4e0536c092aab1a4f (remote main rechecked).
Work branch: feat/carrot-readonly-signal-contract.
Reference: https://github.com/ajouatom/openpilot, refs/heads/carrot-wip at
604bc0a22733e648ec05b268da1ffaae7db52a69. Fetch/ls-remote agree; no movement
since the user's last observed SHA, so the intervening commit range is empty.
Sources are read as pinned Git blobs in the sibling reference repository; no
reference program is executed or installed. No source bodies are copied here.

## Approach and hard gate

Trace schema -> producer -> consumer -> downstream boundary before assigning
meaning. A name-only field match or a transport valid flag is not authority.
Source fields, source-derived interpretations and proposed future policy must
remain distinct. Every normative evidence link pins repository, SHA, path and
line/symbol. Record SHA-256 over raw Git blob bytes, not worktree line endings.

Audit found controlsd computes and publishes a requested latActive/log active,
but card can clear that request later and publishes previous actuatorsOutput
without applied activity or a command-cycle identifier. selfdrive enabled/active,
cruise and panda controlsAllowed cannot close this evidence gap. Snapshot
control_active remains None: BLOCKED_CONTROL_ACTIVE_SEMANTICS.

Published saturated is a timer-qualified controller alert with speed/override/
limiter exclusions; MEB angle state is explicitly dummy. A false alert does not
prove absence of current limiting. Preserve that distinction and require an owner
resolution: BLOCKED_SATURATION_SEMANTICS for a universal learning-admission flag.
Document narrow source-alert candidates without approving them as Snapshot values.

Decision: CONTRACT_BLOCKED_REQUIRED_SIGNAL_UNRESOLVED. No carrot_contract.py,
mapper, controller enum implementation, adapter package or mapping tests will be
created. Remaining deliverables are independently written audit documents,
synthetic evidence fixtures and static evidence validation plus existing regression.
Do not represent the synthetic cases as executed adapter behavior.

## Deliverables

- [x] Pin and hash the actually inspected source/schema/publisher/consumer files;
  record embedded opendbc tree/symlink layout and license/attribution limits in
  carrot_provenance.md plus carrot_source_manifest.json. Atomic docs commit.
- [x] Complete all Snapshot rows in carrot_signal_contract.md with exact sources,
  types, units, sign limits, clocks, health, unavailable behavior and confidence.
  Include controller-aware saturation and baseline classification tables, source
  validity composition and age-at-anchor arithmetic without vehicle defaults.
- [ ] Record 16 independent synthetic scenarios, explicit rejection and None
  semantics, timestamp/age arithmetic and unchanged injected baseline. Validate
  evidence JSON statically; no product mapper or runtime result is claimed.
- [ ] Update the integration index/roadmap with the blocked decision and remaining
  evidence needed for a later owner-authorized Phase 8B. No later phase starts.
- [ ] Run full regression, lint, format, strict types, package coverage floors,
  replay goldens and build. Review the audit evidence independently, commit/push
  normally, create Draft PR and inspect exact-head CI. Keep working tree clean.

## Review focus

Do not confuse algorithm/request activity with final actuator permission; a false
timer alert with an unconstrained controller; Event.valid with upstream estimate
health; publication age with physical sensor age; or estimator output with the
actual privately overridden runtime baseline. Missing facts stay None or reject.
No source or vehicle-specific bounds become defaults. Attribution is not inferred
from a top-level license alone, and no target LICENSE is chosen.
