# Pure preparation-profile supplied-claim contract v1

## Scope,choices and fixed non-authority

Freeze an implementable neutral test-only claim family for the preceding
H-preparation blueprint. This is data/type/wire/assessment design,not a reader,
collector,provider,launcher,host/toolchain/syscall policy,execution admission or
H1/application bridge. No package is implemented by this artifact task.
Generic dictionaries and reuse of H1/runtime types are rejected;separate exact
frozen/slotted DTOs and a pure comparator are selected. Caller claims,hashes,
matching booleans,user autonomy and a clean review never establish execution.

Profile identifier:H_PREPARATION_PROFILE_V1. Wire version:
preparation-profile-claims-v1. All public DTOs/policy/records/decisions expose
fixed status=BLOCKED,integrated_admission=false,content_identity_only=true,
H_executed=false,atomicity=NOT_ESTABLISHED and the literal9false permissions from
the original H1. These are derived read-only facets,not constructor/wire inputs.
Retain all prior H/Q/I,ENTRY/exact-I/STACK,inventory/budget/toolchain/enforcement,
custody/D01-D04,vehicle/science/application blockers and operationalI1/original
host Git-config equality UNCONFIRMED. Nothing modifies old metadata or v1 meaning.

## Primitive rules

Only exact types,not bool-as-int or subclass/duck types. Integers are UInt64
0..18446744073709551615;this is representation width,not a runtime safety budget.
Unknown is None. Budget0 is representable known data,and must be rejected as a
nonpositive required limit during assessment rather than changed to unknown.
Known unlimited is the exact string UNBOUNDED,not None or 0. No float is accepted.
Control claims are exact bool or None;False is available negative evidence.

Hex identities use exact lowercase40(revision/tree),64(digest),32(run_id) characters.
Clock domain is None or exact ASCII text1..128characters from A-Z/a-z/0-9/._:-,
not a timestamp/branch/object address. Paths/argv/hostnames/credentials are absent
from these DTOs. Tokens identify content/contexts only;the contract does not prove
how an opaque identity was generated or authenticate its producer.

Sequences accept exact tuple only;copy to new tuples,own nested exact frozen DTOs,
reject duplicate identifiers,and normalize keyed tables into registry order.
Unknown whole table=None differs from explicit empty tuple. Every non-null table
claims a complete inventory;missing known slots in such a table are semantic
TABLE_INVENTORY_MISMATCH,not filled with defaults. Unknown or duplicate identifier
entries are malformed ValueError before assessment. Complete known-key tables may
carry None values. Duplicate identifiers are ambiguous structure:ValueError.
Revalidate the whole exact object graph at every assessment and serialization,
including forged object.__new__/object.__setattr__ instances. This is not same-UID
adversary security or proof Python frozen objects cannot be bypassed.

## Closed registries

registries.json is normative for ordered artifact roles,batch/command limits,
control IDs,command/cohort pairs and original cohort pins. No manifest may extend
these registries at runtime. Limits carry exact registered units;wrong units or
unknown names are malformed ValueError,not implicit conversion.

Eleven artifact roles bind executor,bootstrap,provider,syscall,collection,
toolchain,dependencies,snapshots,expectations,commands and scope-record CONTENT.
The scope-record hash is not AuthorizationGrant or an admission decision.

Batch limits retain the blueprint's12names/units. Per-command limits have7names,
covering memory,PID/thread,CPU usage,scratch bytes/inodes,retained output and wall
duration. Either supplied side declaring a per-command value above its corresponding
known batch cap has LIMIT_SCOPE_INCONSISTENT. Unknown comparisons stay unknown.
CPU quota/period is bandwidth,not cumulative usage. This comparator compares
declared claims;it does not measure CPU/enforcement/latency/overshoot.

All14control IDs represent claims,not attestation. In this profile their expected
posture is True. False in either record or policy is a known contradiction even
when the other argument/field is unavailable. None is unknown. The read-only
GitHub preflight's W_OK/security/API metadata is not automatically mapped to
these control claims or imported by this package.

## Exact DTOs — field order and annotations

Every class below is frozen=True,slots=True and inherits the fixed facets above.
Field names/order are exact;annotations use Python3.12 unions and tuple types.

ArtifactPin(role:str,sha256:str|None)

LimitValue(name:str,unit:str,value:int|str|None)
Only UNBOUNDED is an accepted string value. Nonnegative UInt64 ints are structural
values;the positive-budget requirement is assessed,not silently coerced.

ControlClaim(name:str,value:bool|None)

CohortPin(cohort_id:str,revision:str|None,tree:str|None)
cohort_id is O or D. Well-shaped wrong revision/tree is assessable contradiction.

BoundaryRef(identity_digest:str|None,generation:int|None,clock_domain:str|None)
Generation0 is valid identity data,not unknown. Identity is non-identifying content
metadata,not a PID/path/ownership grant or kernel-handle proof.

TimingClaim(start_ns:int|None,deadline_ns:int|None,clock_domain:str|None)
These UInt64 values are monotonic absolute instants,not budget durations.

CommandProfile(command_id:str,cohort_id:str,boundary:BoundaryRef|None,
limits:tuple[LimitValue,...]|None,timing:TimingClaim|None)
command_id is one of the six registered IDs;cohort_id is O/D. A known mismatched
pair is assessed as COMMAND_CONTEXT_MISMATCH,not silently reassigned.

PreparationProfilePolicy(profile_id:str,run_id:str|None,
artifacts:tuple[ArtifactPin,...]|None,cohorts:tuple[CohortPin,...]|None,
batch_boundary:BoundaryRef|None,batch_limits:tuple[LimitValue,...]|None,
commands:tuple[CommandProfile,...]|None,controls:tuple[ControlClaim,...]|None)

PreparationProfileRecord(profile_id:str,run_id:str|None,policy_digest:str|None,
artifacts:tuple[ArtifactPin,...]|None,cohorts:tuple[CohortPin,...]|None,
batch_boundary:BoundaryRef|None,batch_limits:tuple[LimitValue,...]|None,
commands:tuple[CommandProfile,...]|None,controls:tuple[ControlClaim,...]|None,
producer_errors:tuple[str,...],producer_unavailable:tuple[str,...])

profile_id is exact nonempty ASCII identifier1..128characters using the clock-domain
alphabet;unknown profile IDs are well-shaped but assessment rejects them. Producer
errors may contain only PRODUCER_REPORTED_FAILURE;producer_unavailable only
PRODUCER_REPORTED_UNAVAILABLE. Both are unique tuples normalized lexically.

ProfileReason(code:str,subject:str)
code is one of the respective closed error/unavailable codes in assessment.json.
subject is a derived closed field locator,not arbitrary producer text:profile_id,
run_id,policy_digest,producer,one root table,or a registry locator defined below.

PreparationProfileDecision(errors:tuple[ProfileReason,...],
unavailable:tuple[ProfileReason,...])
Sort/deduplicate reasons by(code,subject). Decision construction rejects a code
in the wrong category or a nonregistered subject. consistency is REJECTED when
errors exist,otherwise UNAVAILABLE when unavailable exist,otherwise
STRUCTURAL_PROFILE_MATCH. No decision carries executable capabilities.

Policy.profile_id may be different well-shaped text so the evaluator can reject
it;source pins and command pair coherence remain fixed universal expectations.
Neither a foreign policy nor None may waive a known universal contradiction.

## Wire/canonical encoding

API:
canonical_policy(policy:PreparationProfilePolicy)->bytes
decode_policy(raw:bytes)->PreparationProfilePolicy
canonical_profile(record:PreparationProfileRecord)->bytes
decode_profile(raw:bytes)->PreparationProfileRecord
assess_profile(record:PreparationProfileRecord,
               policy:PreparationProfilePolicy|None=None)->PreparationProfileDecision

Envelope is exactly {schema,kind,body}. schema=preparation-profile-claims-v1;
kind=POLICY or RECORD,matching the chosen decode function. body contains exactly
the named fields for that DTO above. Nested DTOs become exact field-name objects;
tuples become arrays;None becomes JSON null. No computed facets,decision,status,
permission,authority,hash-of-self or unknown key is serialized. Decoder rejects
missing/unknown keys,duplicate JSON keys,wrong kind/version,nonfinite constants,
floats anywhere,invalid UTF8,UTF8 BOM and malformed exact graph. raw must be exact
bytes,not str/bytearray. All JSON object key order and insignificant whitespace
are accepted;table order is normalized to normative registry order. No trailing
data after the one JSON value. Structural errors raise ValueError,never effects.

Wire input is bounded to1,048,576bytes,nonempty;this is an engineering codec
capacity,not a H resource budget or scientific cutoff. Oversize fails before
parse. JSON/Unicode/nesting/overflow parsing failures become ValueError. UInt64
numbers are exact decimal JSON integers;no IEEE754 rounding/transit is accepted.
Metadata expresses UInt64max as a decimal string to avoid lossy JSON tooling.

Canonical UTF8:json.dumps(value,sort_keys=True,ensure_ascii=True,
separators=(',',':'),allow_nan=False).encode('utf-8'),no trailing newline.
Object field order and valid keyed-table input order do not change canonical
bytes;unknown/empty/zero/False/UNBOUNDED remain distinct. Wire encoders revalidate
all nested exact types. Policy digest is SHA256(canonical_policy(policy)) and is
stored only in Record.policy_digest,never in the policy itself. This is content
identity,not authenticity,trust,custody or execution/application authorization.

## Pure assessment rules

assessment.json defines exact reason codes/locators and traversal. Always validate
record and any non-null policy first;malformed values raise ValueError. Do not
stop at first missing value:collect independent known contradictions on both
sides and keep unavailable reasons beside them. No clock,IO,network/process,
source loader,H1/application/product import or dynamic registry lookup is allowed.

For each supplied side,universal checks require profile ID,original O/D pins,
six command/cohort pairs,complete non-null table inventories,positive finite
limits,True controls,and coherent command timing/boundary clocks. A null whole
table or null scalar/entry is unavailable,not a permissive default. Non-null
table inventory errors never hide available member contradictions;check all
well-shaped members even when an inventory or policy is incomplete.

Per side,known command deadline<start rejects. When command wall duration and
start/deadline exist,checked UInt64 start+duration must equal deadline;overflow
rejects. Unknown duration/start/deadline is unavailable. Policy and record timing
fields compare only when both are known;the policy may contain unknown actual
instants and is then unavailable. This model deliberately cannot turn prepared
but unobserved timing into a complete match. Batch/command/timing clock domains
must agree where known;no wall/CPU counter substitution. Generation0 is valid.

Match policy/record values by keys,not tuple position;null on either side is
unavailable,and unequal available values reject. Both supplied run IDs must
match;artifact and source digests,limits,boundary identity/generation/domain,
command context and timing compare exactly. No pooling across epochs. Record
policy_digest must equal the canonical supplied policy digest if both exist.
Missing policy adds POLICY_UNAVAILABLE but never bypasses universal checks.

No runtime proof is inferred from correct claims or booleans. Scientific
selection thresholds,F/C recommendations,application bounds and owner authority
are absent. All example vectors are SYNTHETIC_SUPPLIED_CLAIMS_ONLY,never real
resource-budget proposals or kernel/host/test-execution evidence.

## Scope and next implementation

scope-registration.json freezes14new paths and2modified scope-consumer files for
a later exact implementation diff. It is not a present guard change or authority.
The old repair209edaa..db915 range remains separately frozen;old helpers retain
their exact bodies. Current whole-range tamper hooks still run and are compared
against the verified frozen+successor status composition. No test is skipped,
deleted or relaxed. implementation-plan.md specifies the narrow modifications,
new negative controls and fixed minimum98statement/95branch coverage for the
new pure package,without changing any old floor.

Next single task:implement this pure family and the exact successor registration
with RED->GREEN tests,then independent exact-head review. Do not implement a
collector/provider/launcher or connect application/H1 admission. No execution
of historical O/D,vehicle/Params/controller/schema/estimator/owner/longitudinal,
policy/config/token change,privileged fallback or paid infrastructure occurs.
