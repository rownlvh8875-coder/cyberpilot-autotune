# NR-M1 offline reference-path Unicode fix

Approved task: fix PR19 NR-M1, continuing PR20 at
feac824124966940d6ec2c541127f466b0c5221b. The Git alternate object-path environment
value currently uses JSON ASCII escaping; Git's C-quoted path parser rejects
Unicode `\u` escapes. Preserve UTF-8 characters while retaining existing quote,
backslash and ASCII whitespace escaping: `json.dumps(path, ensure_ascii=False)`.

Selected minimal encoding fix, rather than copying native objects to an ASCII
location or changing content/digest semantics. An ASCII workaround keeps the
portability defect and expands IO. No new API, normalization, schema or producer.

Acceptance: actual Git reconstruction through temporary bare references named
with Korean, accented Latin, CJK, emoji, decomposed accents and ASCII spaces
returns the exact existing content record. CLI and Unicode temporary overlay
paths work. Reference/backing objects and metadata remain unchanged. Fixtures use
read-only alternates to the warmed exact-R cache, not new project checkouts.

Only the offline registration encoding line changes; add regression tests and
result/plan docs. Do not modify native assets, installed package, old tests, CI,
source evidence, registry policy, prior PR heads or main. Native R c213, C f5e4,
patch/applied tree/synthetic candidate/schema digests and false permissions stay
fixed. No vehicle, Params, SubMaster, estimator/application bridge, deployment,
merge or native-fork PR. No new dependency/setup change needed.

Execute the already-approved scoped fix inline with TDD; one final independent
review and stacked Draft PR against PR20. This is path portability, not source,
device, runtime, empirical or application qualification. Stop after delivery.
