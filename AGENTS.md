# Native E research snapshot — agent instructions

This standalone branch is for CyberPilot native E research only. It is not the product main tree.
Read CLOUD_HANDOFF.md and CLOUD_NEXT_TASK.md before implementation.
Do not import Carrot/Jetson instructions from a different checkout.

- Preserve original snapshot source/tests/reports. CLOUD_SOURCE_MANIFEST.json records135 originals.
- Verify all135 before work; then freeze133 non-ledgers and preserve the original prefixes of the two ledgers.
- CLOUD_VERIFY.py is an initial baseline check; do not rewrite its manifest after legitimate ledger appends.
- Append to PLAN.md and PROGRESS.md; add successor modules instead of rewriting frozen evidence or guards.
- Reuse existing native/bootstrap/framing/manager/intent/D helpers after checking their real semantics.
- The next task is dynamic owner/job binding in a private synthetic sd-bus fixture, not actual manager deployment.
- No sudo, admin elevation, root-user workaround, global packages/settings, daemon reload or service lifecycle.
- No new systemd unit/cgroup/controller writes, credential changes, Docker, SSH/network exposure or device access.
- No actual H/product/vehicle payload, candidate generation, estimator qualification or application bridge.
- No arbitrary caller command/path/PID/FD/unit/receipt launch or ownership recovery API.
- Unknown/unavailable results remain unknown/null, not invented false/zero or cleanup success.
- Supported pure unit/encoding tests, new research source and fixed private fixtures follow the handoff gates.
  If current EUID0 or native controls are unavailable, do not run native F/E/W fixtures; continue pure work.
- Use only existing Python3.12.3..<3.13/compiler/runtime and a new venv; no OS package install.
- A prior local647PASS/real-kernel lab observation is not a new Cloud PASS or qualification.
- All14 flags remain false; provider_registration=UNBOUND;16 required qualification evidences UNAVAILABLE.
- Never delete old residues, reconnect using names/receipts, or repeat an uncertain cleanup.
- No main/PR8/PR9 changes, force push, rebase/reset of existing work, raw log/data upload or external AI service.
- New implementation may make local append-only commits on its research branch; no automatic PR/merge/push.
- Finish the concrete implementation/test/review/report bundle without routine approval menus.
