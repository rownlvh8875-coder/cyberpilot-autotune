# Registered preflight -> preparation-profile read-only mapping design

## Intent,chosen architecture and non-goals

Audit exactly what the existing saved preflight can contribute to the implemented
preparation-profile contract without converting host diagnostics into H evidence.
This task creates a design/catalog/plan,not a parser,adapter,producer or new run.

Considered:direct renaming/coercion(wrong scope);emit an all-null H receipt(no H
identity and misleading capture implication);selected separate registered-source
diagnostics plus a complete target-gap catalog. `profile_record` is fixed None.
All9permissions,false H_executed/integrated_admission,content_identity_only=true,
atomicity=NOT_ESTABLISHED remain fixed. A source match never means H readiness.

The future mapper is deliberately REGISTERED_SNAPSHOT_DIAGNOSTIC_ONLY for
REGISTERED_PREFLIGHT_R0. It does not accept another run/host/attempt as a silent
replacement. The only other explicit profile,SYNTHETIC_MAPPING_S0,is a reserved
fictional fixture for CI,always labeled synthetic and never an R0 fallback.
New real snapshots require separately reviewed source-instance registration;
same schema or identical collector bytes alone do not establish the same cohort.

No H1/ENTRY/preparation-profile/application/owner runtime bridge,OS reader,network,
subprocess,filesystem/clock probe,collector,launcher,policy/budget invention or
vehicle/Params/controller/schema/longitudinal change. No PR60/8/9/main/ref change.

## Exact source binding

Source:actions-runner-preflight-v1,workflow405774698,run41653951704,attempt1,
job125979186623,server head4b77b31dd23010f2d2b394466d88b04a4a2720e2.
API metadata and one JSON line from a newly downloaded job log match saved
observation bytes2998/SHA2564b6aa465bacb157eee17852fdacc5f4da69d7e9401d027f6db3cafa741929597.
No dispatch/rerun was performed. CLI log output was empty;the job-log API returned
the retained log. There is no reconstruction from summary prose or invented data.

Workflow inline collector is byte-identical to tools/actions_runner_preflight.py.
Both files are unchanged between source4b77 and target contract0ac6e3519ad7191b036eb777b4317174121851bb.
sources.json pins repository/revision/path/blob/file hash/function ranges. No checkout
occurred in this workflow. Source source_revision describes workflow source,not an
O/D snapshot consumed by an H execution. Caller execution_context stays unverified.

API/run/job/hash agreement is content/provenance consistency,not authenticity,
private cgroup ownership,clock atomicity or successful H execution. Archived dates
are wall-clock provenance only,not monotonic command start/deadline values.

## Exhaustive field accounting

mapping-matrix.json contains all105 source scalar leaves and all274 target rows:
272 scalar leaves from the complete synthetic target shape plus2 producer streams.
142 are static registry/schema configuration,not observed facts.130 H value slots
and both H producer streams lack the required evidence. Mapped H values:0.
The matrix is a catalog,not a malformed receipt body with None injected into
required strings. No target DTO is instantiated. No target policy is manufactured.

| Target requirement | Slots | Why preflight is insufficient |
| --- | ---: | --- |
| H batch identity / installed policy digest | 2 | Actions run ID is a different identity;no H policy |
| reviewed complete artifact roles | 11 | one tool hash is not executor/provider/inventory/closure |
| consumed O/D cohort / command cohort | 10 | source SHA and frozen expected pins are not consumed snapshots |
| owned batch/command boundary identity/generation/domain | 21 | membership is not private H placement/ownership |
| batch and command budgets | 54 | caller cgroup controls/workflow timeout are wrong scope |
| H monotonic timing/alignment | 18 | API wall time/timeout have no matching monotonic H cohort |
| exercised H controls | 14 | API presence/collector flags are not workload enforcement |
| H producer error/unavailable streams | 2 | preflight diagnostics are not an H producer stream |

Static configuration includes profile ID,registered table names,units,command IDs
and O/D identifiers. It cannot be counted as a captured source/parameter cohort.
142+130+2=274 does not mean274 measured signals or132 executed failed tests.

## Semantic redlines

- memory.max=max and cpu.max='max 100000' remain known source-context strings.
  They cannot become H UNBOUNDED budgets. pids.max=17441 is not an approved H PID cap.
- effective_write_access=False is the collector's W_OK result,not proof of immutable
  mounts,delegation impossibility,read-only H input or provider incompatibility.
- write_delegation_verified=False/atomic=False/qualified=False are declared absence
  of qualification in this producer;there was no write probe. Do not turn them into
  measured failures of a future H provider or fill H controls with False.
- membership_confirmed=True is membership of this observer,not pre-payload gate,
  batch placement or an owned generation-stable private boundary.
- NoNewPrivs=0/Seccomp=0/CapEff zero are available source-process facts,not nulls;
  they are not observations of a different future payload's security posture.
- native APIs True means attribute/import presence,not an exercised syscall,FD
  policy,cleanup,containment,network denial or guard compatibility.
- old setpriv actual hash differs from expected:retain known legacy-pin mismatch.
  bwrap/Codex-Python null reads are unobservable content,not proof binary absent.
- runner timeout2minutes is a job-level wall bound,not any of12 H batch budgets,
  per-command wall/cleanup policy or measured elapsed/remaining monotonic time.
- execution_context.run_id/source SHA cannot be padded/hashed into H identity,cohort or
  generation. Registry O/D constants cannot be substituted for consumed provenance.
- installed prepared policy,toolchain/dependency/snapshot/full expected node inventory
  are absent. Do not generate their digests from this diagnostic report or log.

## Proposed pure diagnostic interface

mapping-contract.json fixes five frozen/slotted DTOs,one pure function,reason and
subject inventories,strict source shape and privacy allowlist. No source reader
or target receipt serializer is provided. Raw bytes are supplied by a caller.

`map_registered_preflight(raw:bytes,binding:PreflightRunBinding|None=None,
 *,source_profile_id:str='REGISTERED_PREFLIGHT_R0')
 ->PreflightMappingDecision`

Result source_consistency is REGISTERED_SNAPSHOT_MISMATCH when known errors exist,
UNAVAILABLE_BINDING when independent binding facts are missing,otherwise
REGISTERED_SNAPSHOT_MATCH. All paths still mean DIAGNOSTIC_ONLY/NO_H_RECORD.
Known legacy pin mismatch is a source diagnostic,not missing data and not an H
control value. It can coexist with a matching retained source snapshot.
Future CI embeds only explicitly fictional S0 input,not the real R0 blob/UID/GID.
The actual R0 bytes are supplied externally for its separate local retained-input
check;the current offline audit already verifies their exact content/provenance,
not behavior of an unimplemented future mapper. The same pure algorithm handles
both explicit profiles;S0 cannot be reported as observed R0 or real execution.

## Privacy and representation

Expose only83 exact JSON pointers from the105-leaf source schema. Exclude all22
UID/GID/euid/egid leaves;unknown keys are rejected rather than copied to diagnostics.
Pointers use RFC6901 escaping for slash-bearing tool paths;never use them as files.
Decision/diagnostic outputs exclude the raw blob and22identity leaves,and unknown
keys such as VIN/GPS/driver fields are rejected. All40string-capable pointers use
closed per-pointer vocabularies drawn only from the registered R0/S0 nonidentity
facts. Well-shaped unexpected text becomes [REDACTED_UNREGISTERED_SOURCE_TEXT]
with SOURCE_TEXT_REDACTED meaning and AVAILABLE status,not None. A redacted marker
may intentionally fail the original hex/control grammar;it is permitted only as
this explicitly tagged output representation,never as a raw-source grammar change.
Constructor and forged-graph revalidation enforce the same text policy.

Raw-byte identity,context and declaration comparisons happen before redaction,
so known errors and exact content digest survive without echoing unexpected text.
Error messages/subjects are fixed and do not log or quote inputs. This is a
field/rawblob/controlled-text policy,not universal DLP for disguised numeric data,
covert channels,input object representations or compromised Python memory/processes.
Exact source byte digest is content identity only,not a privacy/authenticity proof.

None,False,typed0,registered empty string and max are kept distinct. Unregistered
strings may be redacted while remaining known/available. No float coercion or empirical
thresholds. The existing collector's32768byte output cap is the future parser's
engineering input bound,not a safety budget. Hash raw bytes including newline;
JSON reordering may parse but does not preserve registered byte identity.

## Future scope,tests and unresolved prerequisites

scope-proposal.json proposes a separate10A2M successor from0ac6,not a change to the
current14A2M ceiling. Existing PR60 remains Draft and untouched. Future work stacks
from its exact head unless separately adopted main is verified first. New source
helpers live only in the new scope-test file,not appended to old modules.

Freeze old profile4b77..0ac6 and cancellation209edaa..db915 independently;retain
the literal raw4b77..current and209edaa..current calls and untracked hooks. Compare
both with exact old+new status compositions. Only the global history consumer and
the profile final-inventory consumer need modification;all other old helper/test
bodies/top-level AST/thresholds remain unchanged. Future final inventory is exact.

Acceptance cases are PLANNED_NOT_EXECUTED;offline audits and current regression
are not execution of that future adapter or original O/D/H. Required future package
coverage remains>=98statement/>=95branch,no exclusions/old floor changes.

All original H prerequisites,operationalI1/original host Git-config equality,
Q/I/ENTRY/exact-I/STACK,custody/atomicity,toolchain/enforcement/budget,vehicle/science/
application blockers remain. This task does not solve missing provider authority.
