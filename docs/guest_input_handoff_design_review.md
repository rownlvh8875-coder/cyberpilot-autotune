# Independent handoff design review / one author fix pass

Fresh reviewer gpt-6-astra high, read-only, no subagents or target execution.
Exact range `0652c87c5e1da83d2cf4a3336713b9839e929ae3..d45c002f23df62cb463836691cd2c1477f313747`.
Verdict **C0/I1/M3, with fixes**. Independent focused105, audit57cases/7files/
11ranges and1492 malformed-leaf probes passed/rejected correctly respectively.
No independent full/coverage/wheel/CRLF/native/remote-CI rerun was claimed.

## I1: selected exec lacked a pre/post cohort relation

The original graph labeled pre-transfer inventory and post-exec consumer bindings
with one immutable consumer identity and permitted TRANSFER→BIND without modeling
the selected controlled exec. A producer could not tell actual event-local actor
identity from a planned final cohort. This was a design gap, not a demand to
implement the runtime backend.

Author verified16 failing regressions before fixing it. Graph/semantic schema now
v2; inventory digest v2 includes actual cohort. Context declares bootstrap and
post-exec expectations; event-local observations must match the applicable one.
Mandatory EXEC_TRANSITION binds transfer generation plus exact predecessor and
successor task/image/table cohorts: same task, one exec-generation increment,
no inferred table increment. Missing/wrong/stale/duplicate transitions and missing
cohorts reject; v1 has no silent fallback. New positive case explicitly changes
FD-table identity. Input-set and bundle domains retain unchanged v1 meanings.

One author fix pass; no independent fix-head re-review or C0/I0 verdict.
Post-fix full2678, focused130 and66 published synthetic cases pass; pure194/194
statements100%,51/52 branches98.08%; src aggregate98.52%. Source/history/native192,
old PR31/32 replay, lint/format450/mypy71+3/build/fresh vanilla+research wheel and
all smokes reran green. Final CRLF/remote CI are recorded separately after completion.

## Deferred minors — deliberately not folded into the I1 fix

- **M1:** `complete(11..16)` fixture helper uses numeric construction order when
  computing canonical lexical member/reference digests. Current published cases
  use at most2 members; future boundary tests need the helper repaired first.
- **M2:** Resource metadata dictionary equality accepts float-equal integer
  limits. The actual reference oracle still enforces exact integer scalars;
  strict schema metadata type checking remains debt.
- **M3:** The machine-readable catalog omits generic event-envelope field
  metadata (`seq/time_ns/context_digest/kind/data`). Normative prose/oracle define
  it, but the catalog is not a complete runtime codec input. Adding required
  cohort definitions for I1 does not fix this separate envelope omission.

## Reviewer scope boundaries retained / author cost if wrong

1. No actual FD creation/reopen/inheritance/CLOEXEC/exec/transport atomicity:
   future kernel transport may behave differently.
2. No actual consumer/task/image/table/OFD identity, pins or complete enumeration/
   coverage: wrong actor/object/capability could otherwise be admitted.
3. No early-read/unsupported/loss/failure-effect prevention: effects could precede
   retrospective rejection; future enforcement must be qualified separately.
4. No new kernel seal/mapping/COW/platform experiment: target behavior may differ
   from the prior referenced cohort.
5. No pathname/compiler/sysroot/search/generated/loader/environment closure:
   undeclared inputs could affect a broader workload.
6. No implementations of partial/stream/mmap/exec/dup/fork/clone/reopen/reuse:
   broader legitimate workloads remain unsupported.
7. No runtime decoder/external framing/collector availability/hostile transport
   exhaustion proof: a real transport could fail outside synthetic tests.
8. No authentication/freshness/anti-replay/cross-session or trusted old-receipt
   bridge: stale/forged evidence must not become authority.
9. No executor/watchdog/output/science/device/vehicle/application authority:
   unqualified actions remain prohibited by all fixed-false permissions.
10. Reviewer did not rerun historical full/coverage/wheel/CRLF/native/remote CI:
    author must supply separate actual evidence, not imply independent execution.
