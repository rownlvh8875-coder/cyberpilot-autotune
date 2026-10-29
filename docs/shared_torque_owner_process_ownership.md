# H4 process and watchdog execution ownership

Selected direction: **HYBRID_CONTROLSDSOLEOWNER_MANAGERLIVENESS**. One serialized
controlsd-domain owner holds the effective tuple; a separately executing,
manager-supervised observer monitors owner/controller progress. The observer
never becomes a competing coefficient writer. This is a future integration design,
not a new runtime process or qualified safety executor.

## Alternatives

Scores (0–5) represent design potential, not measurements or acceptance evidence.
Higher latency scores mean lower expected scheduling/communication overhead.

| Axis | A serialized controlsd owner | B dedicated owner service | C controller-native owner |
|---|---:|---:|---:|
| Survives CyberPilot producer death | 5 | 5 | 5 |
| Own execution/scheduler assignment | 4 | 4 | 4 |
| Proximity to actual controller state | 5 | 2 | 5 |
| Explicit restart/session handling | 3 | 3 | 3 |
| Recovery latency potential | 4 | 2 | 5 |
| Source/IPC migration simplicity | 4 | 2 | 2 |
| Upstream compatibility potential | 3 | 2 | 2 |
| Failure isolation | 2 | 4 | 3 |

A alone cannot detect/recover its own stall. B survives more producer failures
but its state is not automatically the controller's consumed state: IPC needs a
new versioned consume/Ack/readback protocol and cannot fake PR #9's synchronous
port. C is close to consumption but still cannot execute after its own process
dies and needs broader native/lifecycle changes. Select A plus an independent
manager-observed liveness boundary, rather than a second remote tuple owner.

## Death and restart cases

| Event | Who observes/acts | Reference / proposed native result |
|---|---|---|
| CyberPilot producer dies | live owner, supplied independent liveness evidence | active CyberPilot lease recovers known baseline by CAS/readback, latches fault; no automatic grant/rearm |
| torqued dies during its own lease | live owner watchdog | recover known baseline, fault; no fresh fit is inferred |
| torqued dies during CyberPilot lease | owner/source admission host | unrelated producer cannot overwrite lease; required observation freshness must still pass; if required sources fail, veto/recover |
| no producer lease, baseline READY | owner/source host | no estimator adoption from silence; caller still owes baseline/context qualification |
| owner/controlsd stalls or crashes | separate manager-supervised liveness observer | mark owner state unavailable, request approved output containment; coefficient restoration UNKNOWN |
| dedicated observer/service dies | its supervisor/liveness acceptance system | cannot claim watchdog coverage; inhibit admission or execute separately accepted containment |
| controlsd restarts | startup execution owner | new instance/session/generation/baseline epoch and trusted capture; old proposals/grants rejected |
| manager restarts | external startup/session authority | previous progress/evidence cannot authorize rearm; no implicit ownership continuation |
| custom/NN mode requested while leased | owner arbitrator | close old context through known-cohort recovery; requested mode needs fresh epoch |
| actual mode/source/context changes behind owner | actual context observer | fault unknown; permanently forbid old-domain recovery writes |

Normal shutdown must recover/read back baseline before a clean STOPPED result.
The reference stop/disarm operations model this while the owner executes. They
do not simulate a dead process magically calling a Python method. Restart() is
a logical new-domain factory, not a process launcher or physical restoration.

## Independent progress and containment

Future progress evidence must bind owner instance, epoch, completed controller
cycle, installed/consumed revision and monotonic completion time. Emit it after
successful consumption, never from a heartbeat thread able to run while that
calculation is frozen. An observer rejects stale/replayed/foreign-generation
records. It has its own independent executor and scheduling/deadline acceptance.

The supervisor may coordinate recovery only after proving old execution is
revoked and a new independently trusted context/baseline is available. It cannot
write through a stale shared pointer or restore an old epoch concurrently with a
possibly running owner. Output inhibition is distinct from baseline restoration;
neither process death, silence, a restart nor inhibition proves the tuple is T0.

H4 names these responsibilities but does not select/implement a physical actuator
action, change controller safety limits, demonstrate scheduling bounds or qualify
an existing inhibition path. No such guarantee was established by H3. Therefore:

```text
WATCHDOG_EXECUTION_MODEL_UNRESOLVED
EXTERNAL_INHIBITION_EXECUTOR_ACCEPTANCE_UNRESOLVED
```

The reference's caller-supplied owner_alive/active_producer_alive flags model
observations by these external roles. They are not implemented liveness sensors,
permissions, or evidence that owner self-monitoring survives its own death.
