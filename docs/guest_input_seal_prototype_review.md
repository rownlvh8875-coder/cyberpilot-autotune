# Independent review and author fix pass

Fresh reviewer: gpt-6-astra high, one context, read-only, no subagents.
Exact reviewed range:
`ae7b3644984cd5ecc8fbb23532f5ec7e0da3998f..d3549abbff5b7873cf899ad5a24652cea3ed4891`.
Verdict: **C0/I2/M0, with fixes**. Reviewer independently ran focused77 and
kernel6files/12ranges/8capture audit. No host ELF execution or new guest run.

## Important findings and verified author response

I1: IS06's original pathname was unrelated to the anonymous sealed memfd.
An unrelated rename plus mismatch did not prove changed name resolution.
The author now creates a fixed symlink through `/proc/self/fd/<retained-fd>`,
opens it, checks matching dev/inode and records initial BIND+SNAP through FD0.
Only then does the replacement overwrite that alias. Missing/wrong initial
object/snapshot rejects. Positive initial-binding and missing-binding tests
were watched RED (2failures) before the evaluator/C fix.

I2: Runner/audit used substring completion checks. Prefixes, status01,
conflicting failure+success, early completion and unterminated DONE were
accepted even after serial hashes were honestly updated. All5 published replay
regressions were watched RED. Shared pure `parse_guest_capture` now requires
exact unique LF-terminated markers (CRLF accepted), rejects malformed reserved
markers and enforces kernel→capture BEGIN/END→exit0→DONE. Structural parser is
still separate; no substring-repair fallback or inferred successful window.

One author TDD fix pass; no independent fix-head re-review or C0/I0 claim.
Post-fix full2548/2548 and focused94/94 passed; all8 fresh actual guests matched,
source6files/12ranges and capture replay passed. Pure176statements/82branches
100/100, installed src aggregate98.52%. Ruff/format437,mypy71+7, rebuilt static C
-Werror, source/history/native192 and fresh vanilla+research wheel smokes green.
Fresh CRLF and exact-head remote CI are recorded in the final Draft handoff,
not inferred from pre-fix CI. No deferred Minor.

## Reviewer boundaries retained, with author costs if wrong

1. No hostile producer fabrication/authenticity qualification: otherwise forged
   claims could be mistaken for authentic evidence.
2. No host/hypervisor integrity or post-hash race qualification: otherwise
   executed bytes could differ from static hashes.
3. No whole namespace/compiler/sysroot closure; local IS06 binding is fixed:
   otherwise undeclared inputs could enter a future build.
4. No PR30/workload-consumption witness bridge: otherwise wrong consumer/epoch
   could be admitted without independent qualification.
5. No universal executable-mapping prevention from EXEC seal: otherwise executable
   mappings might be incorrectly assumed impossible.
6. Other kernels/architectures/filesystems and real unavailable/EINVAL behavior
   remain untested: otherwise device behavior could differ from this cohort.
7. No comprehensive concurrent-writer/all-FD/effect accounting; counts unavailable:
   otherwise unobserved operations could be missed.
8. Frozen values are not a hostile in-process Python boundary: otherwise callers
   could bypass the value contract or replace functions.
9. No independent authentication of edited manifests: otherwise substituted
   evidence could be mistaken for trusted evidence.
10. Reviewer did not run new guests, host ELF, C/native coverage or remote CI:
    author must verify permitted guest/CI results separately; host execution
    remains forbidden and C/native coverage remains unclaimed.
