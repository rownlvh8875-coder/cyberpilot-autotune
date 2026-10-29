# H4 failure and recovery model

Reference tests inject faults at the real memory-port/authority/clock boundary.
No fixture makes a parameter effect or vehicle-safety assertion.

| Failure | Allowed proof/action | Forbidden inference |
|---|---|---|
| stale CAS or rejected proposal | tuple/revision unchanged; sequence already consumed if structured | retry edited proposal under same identity |
| failure before CAS replacement | snapshot may observe original exact cohort | assume a successful write from an exception |
| replacement succeeds then raises | exact pending tuple/revision/digest may prove install occurred | overwrite a different/partial/foreign cohort |
| bad Ack, correct actual state | fault remains; independently inspect actual cell and perform one known-cohort recovery | treat observed tuple as a clean Ack |
| correct Ack, wrong/unavailable snapshot | no verified state or baseline; FAULTED when inspected by watchdog/recovery | promote Ack or pending cache to readback |
| offset omitted/changed, including signed zero | complete proposal rejects before install | seed missing offset or use tolerance |
| rollback installed baseline but Ack/readback/clock/deadline fails | report fault and unverified result; later observation is separate evidence | report clean restoration solely from requested baseline |
| actual context/mode/epoch change | fault/unknown; no baseline into foreign context | relabel context to make old recovery pass |
| producer death with owner alive and trusted context | watchdog can restore baseline via CAS and independent snapshot | producer self-monitoring after it has died |
| owner/controller process death | supervisor reports loss and requests approved containment; restoration unknown | assume a dead owner executes rollback |
| process restart | independent fresh identity/session/epoch/baseline required | reset high-water and replay old proposals/grants |

CommitAck has no verification bit. snapshot reads the installed cell through a
separate path and returns a fresh frozen logical observation. A healthy watchdog's
verified UNCHANGED result means its current observation is coherent, not that
the values equal baseline. RecoveryResult.verified with BASELINE_RESTORED or a
retained fault reason requires explicit exact baseline readback. None/unknown is
not substituted with defaults. The future native adapter must independently
demonstrate the same observation relationship to the actual controller binding.

## Trust and serialization assumptions

Clock, authority and tuple port are explicitly injected trusted capabilities.
All owner operations and their capability callbacks are single-caller serialized
and non-reentrant; no thread/process safety is claimed. An untrusted caller with
arbitrary Python mutation or a separate port-writing capability is outside this
security boundary. Foreign-state tests model detected corruption, not a sandbox
guarantee against such code. Digests authenticate neither source nor authority.

Current mutation clocks are checked against previous operations and baseline
time. Snapshot reads are side-effect-free and rely on a caller-supplied monotonic
clock; they do not mutate owner high-water. Deadline overruns are detected after
capability return; no blocking operation can be preempted by this object.

No failure causes automatic FAULTED→READY, same-instance reinitialization, hidden
retry, backlog takeover or lease renewal through no-change. A valid new proposal
may renew a still-valid same-producer lease; source freshness and authority are
revalidated. New numeric limits or lease times are never inferred from that fact.

## Unknown context recovery limitation

Reference rollback checks the actual InstalledTuple against expected/pending
cohorts including identity and mode. In real Carrot, a callback or geometry change
outside that cell can invalidate it too. Native integration must bind/read actual
controller context and revoke old-context recovery when it differs. The reference
watchdog accepts actual context as an explicit input and permanently forbids
same-domain recovery after reported actual context/owner loss. A later generic
rollback cannot bypass that latch. A caller must not fabricate the old context
to avoid reporting the loss. Observing real native context remains a required
integration gate, not source readiness evidence.

## Verification scope

Unit tests cover successful/no-change/stale CAS, replay after denial, finite logical
precision, mode closure, lease/source expiry, restart, shutdown, uncertain writes,
wrong Ack, foreign revision/tuple/mode/identity, readback faults and timing at both
sides of install. Property tests exercise revisions, complete tuple and offset
preservation, rejection/nonmutation, one-shot IDs, sticky faults and independent
baseline restoration across operation sequences. Architecture tests prohibit
runtime imports/IO/threads/processes/default policy and keep old H2/H3 evidence
unchanged. The contract manifest indexes these invariants; it is not authority.
