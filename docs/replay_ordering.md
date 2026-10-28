# Ordering and high-water characterization

This fixture characterizes the current conservative fail-closed high-water policy. It does not claim that the availability tradeoff is optimal.

Only replay schema/checker code changed. AutoTuneEngine, SafetyGate and
ResidualStatisticsLearner are unchanged. Evaluation clocks remain monotonic;
repeated/regressed observation identities are valid synthetic admission inputs.
All thresholds/values below are test-only, unrelated to vehicle control.

Sequence high-water consumes the greatest valid sequence even on rejection.
Time high-water consumes the greatest clock-safe capture time, even on a lower
sequence rejection. Future captures cannot advance time high-water, although
their valid sequence identity is still consumed. Admission rejection resets only
learner evidence, not either engine cursor. A repaired rejected sequence cannot
manufacture samples. None in the table means an empty learner evidence window.

| Event | Sequence | Capture / evaluation clock | Actual reason | Sample count | Engine maxima after event (sequence,time) | Following effect |
|---:|---:|---|---|---:|---|---|
| 0 | 10 | 10 / 10 | none | 1 | 10,10 | Normal warmup |
| 1 | 11 | 11 / 11 | none | 2 | 11,11 | Normal progress |
| 2 | 11 | 12 / 12 | OUT_OF_ORDER | None | 11,12 | Duplicate still advances safe time |
| 3 | 9 | 13 / 13 | OUT_OF_ORDER | None | 11,13 | Lower sequence still advances safe time |
| 4 | 12 | 12 / 14 | OUT_OF_ORDER | None | 12,13 | New sequence cannot undo time maximum |
| 5 | 13 | 100 / 15 | FUTURE_TIMESTAMP | None | 13,13 | Future 100 does not poison time |
| 6 | 14 | 16 / 16 | none | 1 | 14,16 | Normal time after future is admitted |
| 7 | 15 | 17 / 17 | CONTROL_INACTIVE | None | 15,17 | Rejected identity consumed |
| 8 | 15 | 18 / 18 | OUT_OF_ORDER | None | 15,18 | Repair cannot add samples; time still advances |
| 9 | 16 | 19 / 19 | none | 1 | 16,19 | Fresh evidence window |
| 10 | 17 | 19 / 20 | OUT_OF_ORDER | None | 17,19 | Repeated capture consumes new sequence |
| 11 | 18 | 18 / 21 | OUT_OF_ORDER | None | 18,19 | Regressed capture cannot lower time maximum |
| 12 | 19 | 22 / 22 | none | 1 | 19,22 | Recovery requires both maxima to advance |
| 13 | 20 | 23 / 23 | none | 2 | 20,23 | Warmup |
| 14 | 21 | 24 / 24 | ACCEPTED_FOR_SHADOW | 3 | 21,24 | One eligible proposal, baseline retained |
| 15 | 22 | 25 / 25 | ACCEPTED_FOR_SHADOW | 4 | 22,25 | One eligible proposal, baseline retained |

Reason priority is the existing gate's priority, not a new replay policy. The
test-only age budget is deliberately wide to isolate ordering from stale vetoes.
Maxima listed here are derived from the unchanged implementation; following-event
reasons and sample counts pin their visible effects. No private engine state is
exposed through the replay API.

## Focused evidence

constant_residual_v1 has 5 events, 3 eligible proposals, no veto and sample counts
1..5. admission_reset_v1 has 17 events, 3 eligible proposals, two override exclusions
and one each invalid source, unknown/inactive control, low speed and saturation.
Every veto clears evidence before a new three-sample window. ordering_high_water_v1
has 16 events, 2 eligible proposals, 6 ordering vetoes, 1 future and 1 inactive.
All focused maximum deltas are 1/2 synthetic unit; every OFF/SHADOW output retains
trusted baseline and no INTERNAL_ERROR occurs.

Expected files pin every event's returned observation_sequence, reasons,
proposal/eligible counts, actual same-run sample count and trusted baseline check,
plus summary and three digests. No expected file is automatically regenerated.
The original 21-event golden_v1 remains an unchanged aggregate historical fixture.
Neither fixture acceptance nor this availability characterization authorizes
persistence, actual vehicle data, application or deployment.
