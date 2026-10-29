# H4 owner state machine

These are reference states, distinct from PR #9's application states. Every row
describes logical in-memory behavior, not an installed vehicle capability.

| Transition | From / event | Result | Effective revision |
|---|---|---|---|
| T01 | UNINITIALIZED + explicit coherent baseline initialize/readback | READY | explicit caller anchor |
| T02 | initialization/readback failure | FAULTED | no install |
| T03 | READY/OWNED + authorized mutating CAS | OWNED, finite lease | +1 |
| T04 | accepted exact no-change | unchanged, old lease retained | unchanged |
| T05 | stale CAS, malformed/stale proposal, unsupported mode or authority rejection | rejected, tuple unchanged | unchanged |
| T06 | successful proposal identity reused or failed structured identity edited | REPLAY rejection | unchanged |
| T07 | another producer attempts active lease takeover | PRODUCER_BUSY rejection | unchanged |
| T08 | new commit discovers expired lease | RECOVERING, no forward install; expiry fault survives recovery | unchanged |
| T09 | watchdog expiry, stale source or active producer death in proven context | baseline recovery then FAULTED | +1 only if tuple changes |
| T10 | watchdog actual context/mode/epoch/owner mismatch | FAULTED, unknown; no guessed overwrite | unchanged |
| T11 | foreign/malformed port state, including simultaneous expiry | FAULTED, unknown | no owner install |
| T12 | normal explicit baseline rollback and independent verification | READY | +1 if restoration changes tuple |
| T13 | rollback Ack/readback/deadline failure | FAULTED, unverified | actual revision may be unknown |
| T14 | post-install Ack exception/bad revision or clock/deadline fault | FAULTED; pending/expected cohort retained | actual install may have occurred |
| T15 | one explicit recovery from a faulted known cohort | FAULTED remains even if verified | +1 if tuple changed |
| T16 | second recovery attempt after fault recovery | rejected; no retry | unchanged |
| T17 | authorized mode request while OWNED | RECOVERING, old effective mode remains | unchanged |
| T18 | recovery after active mode request | DISARMED at original baseline/old mode | +1 if tuple changed |
| T19 | READY baseline + authorized actual mode transition | DISARMED, new mode requires fresh epoch | +1 |
| T20 | explicit same-mode request at READY | unchanged | unchanged |
| T21 | normal disarm | DISARMED only after verified baseline | +1 only if recovery changes tuple |
| T22 | normal stop | STOPPED only after verified baseline | +1 only if recovery changes tuple |
| T23 | missing/foreign state during stop | FAULTED; no clean stop | unknown where unobserved |
| T24 | DISARMED/STOPPED/FAULTED + forward commit | rejected before capability calls | unchanged |
| T25 | explicit restart handoff from terminal domain | new owner READY; old object remains terminal | new caller epoch and revision anchor |

snapshot(), rejected proposals and healthy watchdog inspection never increment
revision. A full tuple CAS is one transition. A caller coordinating several
transitions must observe each revision separately; no compound Ack hides them.
Revision exhaustion faults before install and never wraps. No FAULTED→READY
transition exists within one owner instance. No source or controller restart
silently resets an existing epoch's revision/replay high-water.

## Cycle/event ordering

| Priority | Event | Treatment |
|---|---|---|
| 1 | unknown/corrupt owner cell or closed domain | reject writes; never use recovery to claim ownership |
| 2 | known expired lease | enter recovery requirement before new proposal/mode/no-change |
| 3 | actual source/context/mode/owner change | no baseline write into unproven context |
| 4 | unsupported producer mode or pending mode handoff | reject forward update or perform required known-context recovery |
| 5 | already required recovery/disarm/stop | complete baseline verification before any handoff |
| 6 | expected-revision conflict | reject without changing tuple |
| 7 | proposal age/identity/authority/shape error | reject; structured sequence remains consumed |
| 8 | no-change | no install or hold renewal |

Within ordinary proposal validation, sequence reservation precedes later context/
mode/CAS/age checks, as in PR #9's fail-closed replay principle. The priority table
does not claim every malformed object receives an identical reason. Closed or
corrupt domains and known expiry are checked first so a new object cannot mask
them. Even when expiry is the primary reason, recovery still requires known
actual context; otherwise report unknown and make no baseline overwrite.

The caller must run watchdog/terminal-event handling before admitting a new
proposal, and perform post-capability timing/context checks before consumption.
This is a future scheduler obligation, not a timer/thread inside the reference.
The selected producer must not be chosen by confidence ranking inside the owner.
