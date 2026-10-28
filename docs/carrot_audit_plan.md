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
- [x] Record 16 independent synthetic scenarios, explicit rejection and None
  semantics, timestamp/age arithmetic and unchanged injected baseline. Validate
  evidence JSON statically; no product mapper or runtime result is claimed.
- [x] Update the integration index/roadmap with the blocked decision and remaining
  evidence needed for a later owner-authorized Phase 8B. No later phase starts.
- [x] Run full local regression, lint, format, strict types, package coverage
  floors, replay goldens and build. Obtain an independent read-only audit review
  and correct its findings. The results are recorded below.

Publication criterion: commit/push normally, create the required Draft PR and
inspect exact-head push/PR CI. The Draft PR checks and final report retain those
remote outcomes and final SHA; they are not embedded as a self-referential commit
hash in these source documents. No Ready transition, merge or later phase is
authorized by this audit.

## Local verification and review record

On 2026-10-28, Python 3.12.14 in the development environment ran the full suite:
475 passed, zero failed and zero skipped. Overall branch-inclusive coverage is
98.53%; safety 100%; residual learner 97.85%; replay 98.48%. Existing architecture,
immutability, admission and baseline invariants are regression checks; no new
mapper behavior is implied. Ruff check and format, strict mypy over 31 source
files, git diff --check, wheel/sdist build and CLI verification of the four
unchanged replay golden fixtures pass.

An isolated wheel environment outside the checkout imported all 31 package
modules and verified the four replay goldens. The rebuilt sdist was inspected:
both new audit JSON evidence files are present and byte-identical to this tree.
The only packaging change includes docs/*.json alongside the Markdown evidence.
Runtime source, dependencies, tests, replay fixtures and CI definitions are
unchanged from the target base.

Static audit validation separately verifies 37 raw Git blobs, 52 upstream source
ranges, 13 Snapshot rows and 16 synthetic evidence cases with exact age arithmetic.
It does not execute or test a mapper. A fresh read-only reviewer independently
checked the same source/fixture evidence and supported the blocked decision.
It found zero Critical, zero Important and three Minor issues: a target baseline
link anchor, an ambiguous age explanation and missing JSON in sdist. All three
were corrected; no runtime code was added to resolve them.

## Review focus

Do not confuse algorithm/request activity with final actuator permission; a false
timer alert with an unconstrained controller; Event.valid with upstream estimate
health; publication age with physical sensor age; or estimator output with the
actual privately overridden runtime baseline. Missing facts stay None or reject.
No source or vehicle-specific bounds become defaults. Attribution is not inferred
from a top-level license alone, and no target LICENSE is chosen.
