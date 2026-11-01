# Approved combined DENY-FD v2 source-first design

User approved local implementation and compile-only verification on2026-11-01(KST): exact1existing+18new paths from the scope below. No guest/host-ELF execution, push, PR or merge authority. Base75fd4358a2d42bec55dc85ba85afbb23e8feb6f9. Branchfeat/deny-fd-v2-source-contract.

Precedence: scope section overrides the earlier proposed package location; use tests/deny_fd_v2/. Historical design-only restrictions and approval-pending statements below describe the design stage; the approved next stage permits only the specified local source implementation and compilation. Other prohibitions remain. External source-anchors/path-routing/proposal JSON references are provenance of the design process, not runtime/build dependencies. Exact39old-image records are preregistered in docs/evidence/deny_fd_v2_history_successor_v1.json; new-source pin M is separate.

## Original producer design (historical wording)

# DENY-FD v2 producer/decoder 패치 설계안

상태: 설계 초안, 구현·실행·게시 승인 문서가 아님.
기준: `rownlvh8875-coder/cyberpilot-autotune` PR54,
`75fd4358a2d42bec55dc85ba85afbb23e8feb6f9`.
이번 산출물은 저장소 밖에 둔다. 저장소 파일·브랜치·기존 PR·main을 바꾸지 않는다.
문서 작성일2026-11-01. 기술 선택은 기존 위임에 따른 작성자 제안이지,
사용자가 아직 보지 않은 세부 설계에 이미 동의했다는 뜻이 아니다.

## 1. 목적과 현재 결함

실제 정지된 guest target의 한 PRE_EXEC_INVENTORY 지점에서 관측한 FD 집합과
그때 사용한 policy 집합의 차이를 producer가 보존하고, decoder가 정확한
원본 FD event로 추적하도록 설계한다. 범위는 point inventory 진단뿐이다.
FD/OFD lifetime observer, 완전한 input closure, handoff 성공 또는 실행 허가가 아니다.

현재 v1 C `snapshot()`133..164는 FD 목록을 관측하지만 마지막에 enum 하나로
축약한다. `deny()`166..169는 항상0을 출력하며, Python `model.py`457..465도
그0을 요구한다. 따라서 HH03의 실제 extra FD3은 목록에 있지만 DENY의 FD는0이다.
또한 현재 INVENTORY_MISMATCH는 missing/mixed inventory까지 포함할 수 있어
새 producer가 이를 무조건 UNEXPECTED_FD로 번역해서는 안 된다.
정확한 repo/SHA/path/blob/range SHA-256은 같은 폴더의 source-anchors.json에 둔다.

## 2. 접근 방식과 선택

- v1 C/decoder/저장 capture를 직접 고침: 기존 증거 코호트와 고정 postimage를
  바꾸므로 제외한다. 과거 HH03을 뒤늦게 FD3을 출력한 실행으로 만들 수 없다.
- v1 로그를 읽어 cause3을 추가하는 overlay: 설명 자료는 될 수 있지만 실제
  producer 출력이 아니다. observed-v2로 승격하는 adapter는 제외한다.
- 별도 버전의 inventory 전용 C producer와 순수 Python decoder: 권장한다.
  원본 v1과 PR54 계약은 그대로 두고 새 bytes에만 새 version/framing을 적용한다.

다른 목적과 충돌하지 않는 선택은 마지막 방식이다. 기존 위임에 따라 이것을
제안한다. 기존 C는 source reference이지 복사 후 이름만 바꾸는 구현 사양이 아니다.
새 producer는 PRE_EXEC 지점에서 끝나며 target을 exec/read/READY로 진행시키지 않는다.
전체9개 v1 handoff case의 새 버전을 만드는 작업은 이번 설계 범위가 아니다.

## 3. 경계와 비목표

새 wire: `guest-data-fd-denial-observed-v2`.
PR54 neutral receipt `deny-fd-provenance-receipt-v1` 및 PR33 qualified-v2와 별개다.
기존 C/decoder/captures/manifest, PR54 package와 policy, src/compatibility/.github,
fixtures/attrs, 기존 PR/head/main은 이번에 수정하지 않는다.

이번에는 C/decoder 구현, scaffold, dependency 설치, compiler 실행, host ELF 실행,
QEMU/guest/kernel/vehicle 실행, Params/controller/cereal schema 변경을 하지 않는다.
새 데이터 수집, qualification, 후보 생성, application/owner bridge, 외부 AI,
longitudinal, upstream PR, merge/rebase/force push도 하지 않는다.

미래 구현의 기본 범위도 source+compile-only+synthetic decoder 검증이다.
실제 guest capture는 그 후 별도 opt-in 작업이며 기본 pytest/CI에서 실행하지 않는다.
새 C가 존재하거나 컴파일되어도 실제 observed-v2 capture가 있다는 뜻은 아니다.

## 4. 권장 capture architecture

고정 C supervisor의 정지된 target inventory 비교 함수가 유일한 capture point다.
Python이 나중에 v1 topic을 join하거나 case 번호로 cause FD를 선택하지 않는다.

1. guest-only scope/kernel guard 뒤 BEGIN과 고정 policy를 출력한다.
2. 단일 child를 fork하여 실제 BIRTH ordinal을 부여한다. child는 descriptor table을
   닫고 TRACEME로 멈춘다. parent는 초기 empty inventory/단일 thread를 확인한다.
3. 고정 bootstrap이 테스트용 FD만 설치하고 기존처럼 UID/GID65534,
   NoNewPrivs1을 설정한 다음 두 번째 SIGSTOP에 멈춘다.
4. parent가 실제 wait/ptrace stop을 확인한 상태에서 PRE_EXEC_INVENTORY를 관측한다.
   이 시점 이후 child를 다시 resume하지 않는다. exec_ordinal은 실제로0이다.
5. `/proc/<child>/fd`를 완전히 열거하고 수집한 각 번호의 FD source ref를 보존한다.
   `/proc/self/fd`를 쓰거나 observer 자신의 FD 번호를 임의로 제외하지 않는다.
   예상하지 않은 FD를 open/read/hash하여 추가 부작용을 만들지 않는다.
   이 계약의 FD witness는 정지 지점의 directory-entry membership이지 object/OFD 동일성이 아니다.
6. 고정 크기 snapshot 구조에 observed set, expected set, row seq/time/ref,
   root/exec/snapshot/policy cohort, actual credentials/thread 상태를 보존한다.
   열거/close/parse/credentials 실패,64FD 초과, 중복, 복수 thread는 완전한 inventory가 아니다.
7. `extras=observed-expected`, `missing=expected-observed`를 계산한다.
   missing이 없고 extras가 있으면 UNEXPECTED_FD와 모든 원본 FD ref를 출력한다.
   둘 다 없으면 NO_DENIAL, missing만 있거나 mixed이면 별도 unsupported 결과다.
8. 모든 정상 진단 경로에서 정지된 child를 종료하고 실제 wait/reap 후 END를 출력한다.
   NO_DENIAL도 종료하므로 handoff/transport success를 뜻하지 않는다.
   syscall entry/target read는 없고 inventory의 operation_fd는 반드시null이다.

정상 진단 capture의 REAP은 실제 SIGNALLED9만 허용한다. 예기치 않은 exit,
clock/logging/kill/wait 오류는 exit2 또는 불완전 raw capture로 남기며 성공 frame으로
수리하지 않는다. logging 오류 함수가 즉시 `_exit`하여 cleanup을 건너뛰지 않도록
실패를 상위 cleanup 경로로 반환한다. 그 경로는 child를 resume하지 않고 종료/reap을
시도한다. 기존 PTRACE_O_EXITKILL 등은 방어 조치일 뿐 qualified watchdog이 아니다.

정지된 한 thread와 두 barrier는 fixed bootstrap 안의 point consistency만 제공한다.
외부 privileged mutation, generic alias/task closure, 지속적 FD-table 추적이나
kernel linearization을 증명하지 않는다. 실제 directory scan interval의 원자성을
한 kernel syscall의 원자성과 같다고 부르지 않는다.

미래 고정 실행 형태는 guest의 `/deny-fd-v2-probe --probe DFD0X`만 제안한다.
새 scope 파일 `/etc/deny-fd-v2-scope`의 정확한 bytes
`deny-fd-v2: fixed pre-exec inventory probe only\n`,root supervisor와
Linux `6.12.113+deb13-cloud-amd64`/x86_64를 guard한다. 어떤 fallback도 없다.
이 guard가 host execution을 안전하게 만든다는 뜻은 아니므로 ELF는 host에서 실행하지 않는다.
미래 실제 capture 작업에서만 기존 QEMU10.0.13 TCG cohort의 정확한 assets를 재검증하고
새 init/image/scope digest를 기록한다. 기존 asset 파일의 현재 가용성이나 새 image와의
동일성을 확인했다고 주장하지 않는다. no NIC/disk/share/KVM/passthrough 조건을 유지한다.
새 init marker와 scope는 새 harness가 소유하며 옛 runner에 새 bytes를 넣어 실행하지 않는다.

## 5. Identity와 source/build 순환 의존 방지

- capture_id: guest supervisor가 성공한 getrandom16bytes를32자리 lowercase hex로 기록.
  실패하면 capture 실패. wall clock/PID/branch/address는 identity가 아니며 random ID도
  freshness/authenticity 또는 권한 증명이 아니다.
- root_birth_ordinal: 실제 fork의 collector-local1. exec_ordinal0은 birth 후 exec가 없음.
- snapshot_id: 이 capture의 한 최종 inventory에 할당한 local1. kernel generation이 아니다.
- slot_observation_epoch,fd_table_generation,ofd_generation은 모두null이다.
  첫 관측이라는 이유로0을 넣거나 inode/hash를 generation으로 바꾸지 않는다.
- sequence는1부터 연속인 UInt64. 각 time_ns는 실제 CLOCK_MONOTONIC observation time.
  읽은 시간이 같거나 역행하면 실패하며 `previous+1`로 보정하지 않는다.
  FD의 time은 해당 membership witness 채집 직후, SNAP time은 전체 채집 완료,
  DENY time은 저장한 snapshot에 대한 결정 후 기록한다. syscall-source time이 아니다.

미래 구현 code commit M의 raw source 파일들에서 사전 source manifest를 만든다.
manifest는 version,repo,M,닫힌 파일 목록(path/mode/blob SHA-1/SHA-256)만 포함하며
ELF/build manifest/raw capture/final image hash를 포함하지 않는다. canonical compact
sorted UTF-8 JSON의 SHA-256을 source_manifest_digest로 정의하고, M과 이 digest를
고정 build command가 compiler 정의로 전달한다. 새 C 본문에 자기 commit SHA를 쓰지 않는다.
M은 구현 후 별도로 확정할 값이며 현재 기준75fd435를 새 C의 source pin으로 쓰지 않는다.
source manifest 자신도 source 파일 목록에 넣지 않는다. M에서 source bytes를 먼저
고정한 뒤 manifest를 생성하고, 기록을 commit한다면 M 이후 별도 append-only commit에 둔다.

post-build manifest는 M,source manifest digest,실제 compiler command/version,
ELF hash/size를 바깥에서 연결한다. 이후 실제 capture envelope가 init/image/VM/raw bytes
hash를 연결한다. ELF hash나 최종 capture digest를 ELF/BEGIN 안에 자기 참조로 넣지 않는다.
이 연결도 content identity이며 toolchain/input closure나 log authenticity는 아니다.

## 6. 닫힌 physical wire 제안

전체 serial은1MiB 이하,LF 종료. 프로토콜 line은4096bytes 이하,총1024events 이하,
expected/observed/causal FD 각각64개 이하. 모두 resource bound이며 safety threshold가 아니다.
CRLF의 단일 마지막CR만 허용한다. splitlines/임의 strip/문자 대체는 쓰지 않는다.

정확히 한 `DFD2_EXEC`, 그 뒤 events, `DFD2_PROBE_EXIT=0`, 바로 다음 `DFD2_DONE`.
그 외 종료 코드/누락/중복/다중 frame은 진단 거부다. frame 밖 boot noise는 보존 가능하지만
reserved DFD2/HFD protocol row나 marker가 섞이면 거부한다. frame 안은 DFD2 row만 허용한다.
각 row는 `DFD2 [seq,time_ns,"KIND",...payload]`인 flat ASCII JSON array다.
v1 HFD/옛 version과 혼합하거나 자동 fallback하지 않는다.

공통 타입: seq/time/root/exec/snapshot/policy/count는 UInt64,FD는0..2**31-1의
exact integer. Bool/Float/지수 표기/NaN/Inf,중첩 container,추가 field,unknown enum은 거부한다.
ASCII token96자 이하,revision은 lowerhex40,digest는 lowerhex64. null은 지정된
nullable slot에서만 가능하다. unknown은0/false/빈 집합으로 정규화하지 않는다.

아래는 공통 seq,time,kind 뒤의 정확한 payload 순서다. `stage`는 이 버전에서
PRE_EXEC_INVENTORY만,root=1/exec=0이다.

| Kind | Payload |
|---|---|
| BEGIN | version,capture_id,source_revision,source_manifest_digest,clock,evidence_kind,case_label |
| POLICY | policy_id,configured_subject_fd_or_null,expected_count |
| EXPECT | policy_id,fd |
| BIRTH | root,exec |
| FD | snapshot_id,stage,root,exec,fd,slot_epoch_null |
| SNAP | snapshot_id,stage,root,exec,policy_id,observed_count,threads,uid,gid,nnp,fd_table_generation_null,ofd_generation_null |
| CAUSE | snapshot_id,fd,fd_source_seq |
| DENY | snapshot_id,stage,root,exec,policy_id,UNEXPECTED_FD,operation_fd_null,cause_count |
| RESULT | snapshot_id,stage,root,exec,policy_id,outcome |
| REAP | root,exec,SIGNALLED,status9 |
| END | root,exec,dropped_count_null |

BEGIN version은 위 v2만,clock은 GUEST_MONOTONIC_NS만,evidence_kind는
OBSERVED_UNTRUSTED만 허용한다. case_label은 아래 고정 case의 metadata이며 인과 결정 입력이 아니다.
POLICY/EXPECT는 실제 소비한 고정 policy context다. expected_count는 exact known count;
0은 빈 policy이며 unavailable이 아니다. 임의 caller policy FD/vector는 받지 않는다.
EXPECT와 FD/CAUSE는 각각 FD 오름차순이고 중복이 없어야 한다.

문법: BEGIN,POLICY,EXPECT^expected_count,BIRTH,FD^observed_count,SNAP,
그 뒤 `(CAUSE^cause_count,DENY)` 또는 RESULT 하나,REAP,END.
전체 capture에 한 policy/한 최종 snapshot/한 결정만 허용한다.
FD refs < SNAP < CAUSE rows < DENY가 seq/time 양쪽에서 성립해야 한다.
CAUSE.fd_source_seq는 같은 capture/snapshot/root/exec/stage의 실제 FD row를 가리킨다.
decoder는 그 row의 실제 time/slot/context 전체를 연결하고 FD 번호만 맞춰주지 않는다.
모든 FD에 정확히 한 witness가 필요하고 declared counts와 실제 row counts가 같아야 한다.
SNAP의 thread=1,uid=gid65534,nnp=1도 일치해야 한다. credentials 불일치는 unsupported capture다.

missing이 없고 extras가 있을 때만 DENY이며 CAUSE 집합은 extras와 정확히 같다.
RESULT.outcome은 NO_DENIAL,UNSUPPORTED_MISSING,UNSUPPORTED_MIXED 중 정확한 set relation과
일치해야 한다. RESULT에는 CAUSE/DENY를 덧붙이거나 missing을 EXTRAFD로 숨기지 않는다.
관측 실패는 이 세 결과로 가장하지 않는다. END의 dropped_count는 항상null이며
연속 seq나 정상 END만으로 lossless/authentic capture를 주장하지 않는다.

## 7. Decoder와 권한 분리

미래 새 package는 `tests/experiments/deny_fd_v2/`를 제안한다.
`contracts.py`,`wire.py`,`validation.py`는 standard-library-only pure functions와
frozen/slots dataclasses,defensive tuples,nested exact validation만 사용한다.
`decode(raw: bytes)`에는 legacy case 변환,caller evidence-kind/source override 또는
application/qualification 옵션이 없다. `check_inventory(parsed)`는 관계만 검증한다.

반환 타입은 ParsedDenialV2/ParsedInventoryV2 같은 untrusted envelope다.
결과는 WIRE_DIAGNOSTIC_CONSISTENT 또는 reasoned REJECTED이며 status는 BLOCKED,
기존9permissions는 전부false 고정이다. 권한 fields가 있는 raw row는 허용하지 않는다.
builder가 세부 함수/enum 이름은 정할 수 있지만 ELIGIBLE/qualified/authorized라는
이름으로 성공을 표현하거나 untrusted를 제거할 수 없다.

원본 bytes가 synthetic test vector인지 실제 수집물인지는 header의 OBSERVED_UNTRUSTED
문구로 증명할 수 없다. synthetic parser fixture는 영구히 synthetic 시험 자료이며
실제 capture manifest에 넣지 않는다. 실제 수집 여부는 별도 acquisition record에서
raw serial과 source/build/image/VM 기록을 연결해 설명해야 하며 그래도 untrusted다.

새 decoder runtime은 v1 parser와 PR54 synthetic evaluator를 import하지 않는다.
이번 단계에 neutral receipt adapter도 없다. PR54 evaluate가 observed 입력을 계속
PRODUCER_NOT_IMPLEMENTED로 거부하는 것은 고정된 옛 API의 경계로 유지한다.
새 decoder 결과로 그 분기를 우회하거나 기존 SYNTHETIC enum으로 cast하지 않는다.
application/owner/estimator/installed src/Params/openpilot/cereal import도 금지한다.
ELF build helper와 미래 opt-in acquisition harness는 pure decoder 모듈 밖에 둔다.
wheel은 이 test-only package를 포함하지 않아야 한다.

## 8. 고정 case와 반례

아래는 미래 harmless fixture의 고정 profile 제안이다. 임의 FD/executable/payload/
command/QEMU args를 public API로 받지 않는다. case는 설치할 고정 입력만 선택하고
DENY predicate는 case 번호를 읽지 않고 받은 snapshot과 policy 차이만 사용한다.

| Label | expected | actual installed | 결과 |
|---|---|---|---|
| DFD01 |0|0,3|DENY cause3,configured_subject0,operationnull |
| DFD02 |0|0|NO_DENIAL;DFD01의 extra 주입만 제거한 counterfactual |
| DFD03 |3|0,3|DENY cause0,configured_subject3,operationnull |
| DFD04 |0|0,3,4|DENY causes3,4 모두 원본 ref 연결 |
| DFD05 |0|empty|UNSUPPORTED_MISSING;빈 inventory는 unknown 아님 |
| DFD06 |0|3|UNSUPPORTED_MIXED;extra3만으로 UNEXPECTED_FD 안 됨 |

관측/clock/serialization/kill 오류는 C의 고정 fault-injection unit seam 또는
mocked harness failure로 시험하되 정상 actual capture로 저장하지 않는다.
이 six-case 목록은 예정된 검증 입력이며 이번에 실행한 결과가 아니다.

필수 decoder 반례:옛 HFD/v1,mixed windows,잘못된 marker/exit/non-LF/VT/FF/중복BEGIN,
oversize/잘못된 arity/enum/clock,negative/Bool/Float/UInt64 overflow/FD overflow,
None vs0 vsempty,누락/중복FD/count,다른 capture/snapshot/root/exec/policy/stage,
future/duplicate source seq,seq와time순서불일치,stale slot ref,잘못된cause subset,
FD0대체,한 extras만 출력,mismatched NO_DENIAL/missing/mixed,REAP/END 누락,
가짜 dropped0/FD-table0/OFD-generation0,synthetic-to-observed/authority 캐스팅.

관계 property:동일 fields의 deterministic digest,source revision/cohort 변경 시
digest 변경,unknown과zero 구별,아무 parser fixture도 런타임 qualification을 획득하지 않음.
새 package statement>=98%/branch>=95%,가능하면100/100. C compile/static/synthetic
시험과 실제 guest/커널 관측 증거를 분리한다. threshold/기준 완화/skip/xfail로 통과시키지 않는다.

## 9. 저장소 통합 전 별도 prerequisite

현재 history policy는 전체 tracked/index/worktree/untracked delta를 정확한40개
경로로 제한한다. 새 문서 한 개도 자동 허용되지 않는다. 기존 policy/fixture의
P2 고정 postimage를 임의 수정하거나 새 directory wildcard를 넣지 않는다.
기존 PR54 branch를 수정하여 이 설계를 끼워 넣지도 않는다.

따라서 이번 외부 설계를 미래 구현에 반영하기 전에 별도 history-successor
사전등록 변경집합과 정확한 existing/new 경로를 사용자에게 보여 승인받아야 한다.
그 prerequisite는 원본 P/P2와 현재40개 코호트의 고정 이력,기존 역사 실행 기준을
보존할 방법까지 검토해야 한다. 정책 확장을 위해 기존 파일 변경이 필수라면
preserved/승인된 modified 경로와 exact pre/postimage를 따로 명시해야 하며,
40개 working postimage 전부를 그대로 둔 채 범위를 확장할 수 있다고 약속하지 않는다.
새 helper를 추가하면 기존 P2 clone test가 저절로 새 pin을
가진다고 가정해서는 안 된다. 이 문서는 그 successor의 수정 권한이나 설계를 대신하지 않는다.

producer 전용 예상 구성은 새 C 한 개,순수 contracts/wire/validation/init,
고정 compile helper,wire/validation/architecture tests,semantic/source manifests,
contract/result 및 승인된 spec/plan 문서다. 이 목록은 component 제안이지 승인된
exact-path whitelist나 새 commit scope가 아니다. exact scope는 prerequisite에서 닫는다.
실제 guest runner/captures/build artifacts는 구현 후 별도 수집 작업의 범위다.

## 10. 완료 판정과 다음 단일 작업

이번 완료는 DENY_FD_V2_PRODUCER_DECODER_PATCH_DESIGN_READY까지만 가능하다.
저장소 통합은 HISTORY_SUCCESSOR_SCOPE_NOT_APPROVED로 차단한다.
PRODUCER_NOT_IMPLEMENTED,OBSERVED_V2_CAPTURE_UNAVAILABLE,
LEGACY_PR34_M1_OPEN,FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED,
WATCHDOG_EXECUTION_MODEL_UNRESOLVED,EXTERNAL_EXECUTOR_UNQUALIFIED,
APPLICATION_NOT_AUTHORIZED와 나머지 기존 empirical/vehicle/runtime blockers는 유지한다.
기존9permissions는 모두false이고 기존 문서의 역사적 상태를 새 문서가 소급 변경하지 않는다.

다음 단일 권장 작업은 producer 구현 자체가 아니라 이 설계에 필요한
history-successor의 exact-path scope 사전등록 설계·승인이다. 승인과 계획 없이
새 source 또는 decoder를 만들어 기존 보존 검사를 우회하지 않는다.

문서의 source audit/관계 검증 계획은 실제 런타임 검증 결과가 아니다.

## 11. 설계 검토 결과

fresh-context builder check의 답변은 `nothing important left`였다. 구현 결과에
대한 C/I/M 코드 리뷰나 독립 런타임 검증이 아니라, 이 문서에서 계획자가 새로
추측해야 할 핵심 질문이 남았는지의 점검이다. 재검토 agent를 추가하지 않았다.

작성자가 정한 세부 선택은 별도 inventory-only v2,C+standard-library Python,
flat bounded JSON,고정6profile,unknown generation은null,source/build/capture digest 분리,
외부 문서 보관과 별도 history-scope 승인 gate다. 아직 사용자 설계 승인을 받은
세부 구현 선택으로 표현하지 않는다. 기존71개 focused tests와12source anchors,
legacy capture/build digest를 확인했으며 새로운 v2 구현을 시험한 것이 아니다.

## Approved exact-path successor design (historical wording)

# DENY-FD v2 exact-path history-successor 사전등록 설계

상태: 사용자 scope 승인 전 외부 설계안. 실제 P3/policy/구현이 아니다.
기준 B:75fd4358a2d42bec55dc85ba85afbb23e8feb6f9(PR54 exact head).
P:127f485437437b3472659784b7b05857d8fbd896.
P2:a7b632f2f331c4029789e2ace7ed8cdb8bb48ca2.
P3는 미래 구현에서 생성할 미정의 commit이다. 임의 SHA/postimage를 만들어 넣지 않는다.

## 1. 목적과 승인 구분

직전 producer 설계를 source-first로 구현할 수 있도록 닫힌 파일 범위와
기존 역사 검증을 보존하는 successor 메커니즘을 제안한다.
이번에는 저장소/브랜치/index/PR/main에 쓰지 않고 외부 설계/metadata만 작성한다.
사용자의 이전 포괄적 위임을 기술 선택의 근거로 삼되, 아직 보지 않은
exact-path scope나 코드 postimage가 승인됐다고 표현하지 않는다.

이번 승인 대상으로 제안하는 범위는 기존1개 수정+신규18개=delta19경로,
기존40개 중39개 preserved, 누적58개다. 이는 glob/directory 허용이 아니다.
scope 승인은 이후 로컬 구현 범위를 닫는 것이며 unseen code 승인,authenticity,
runtime/application 권한 또는 PR 게시/병합 허가가 아니다.

## 2. 접근 비교와 작성자 권장

1. 기존 frozen policy/test fixture의 pin을 새 pin으로 바꿈: 제외한다.
   P2로 checkout하는 기존 테스트의 의미와 고정 postimage를 바꾼다.
2. 새 파일만 추가하고 기존 검사를 무시하거나 directory를 whitelist함: 제외한다.
   새 경로는 현재40개 scope 밖이며 원래 기준을 우회하게 된다.
3. 현재 mutable successor loader1개에 좁은 hook만 추가하고,새 helper가 P3와
   신규18개를 검증함: 권장한다. P/P2 검증·기존 tests·18guards는 그대로 둔다.

이 선택은 작성자 제안이다. 추가 경로가 필요해지면 멈추고 별도 scope 승인을 받는다.

## 3. 정확한 변경 경로

기존 수정은 다음1개뿐이다.

`tests/history_transition/deny_fd_successor.py`

허용할 코드 변화는 새 helper의 명시적 import와 기존 최종 반환식에 검증 결과를
union하는 hook이다. 기존 constants/NEW_PATHS11/P2 pin,29개 검사 본문,Git/CRLF
처리와 error semantics를 유지한다. P3 SHA를 이 기존 파일에 넣지 않는다.
기존 tests/history_transition/policy.py와 tests/test_history_transition_policy.py는
P2 postimage 그대로 두며 수정하지 않는다. 원본P와22postimages도 그대로다.

신규는 아래18개만 제안한다.

| # | 경로 | 역할 |
|---|---|---|
|1|tests/history_transition/deny_fd_v2_successor.py|P3 pin/새 코호트 검증|
|2|tests/test_deny_fd_v2_history_policy.py|신규 실제 Git 반례|
|3|docs/evidence/deny_fd_v2_history_successor_v1.json|immutable P3 manifest|
|4|tests/deny_fd_v2/__init__.py|빈 test-only package marker|
|5|tests/deny_fd_v2/contracts.py|immutable untrusted wire types|
|6|tests/deny_fd_v2/wire.py|strict v2-only pure decoder|
|7|tests/deny_fd_v2/validation.py|순수 inventory 관계 검사|
|8|tests/deny_fd_v2/guest/probe.c|고정 inventory-only guest C source|
|9|tests/deny_fd_v2/build.py|고정 source-bound compile-only helper|
|10|tests/test_deny_fd_v2_wire.py|synthetic framing/type 반례|
|11|tests/test_deny_fd_v2_validation.py|source/cohort/cause 반례|
|12|tests/architecture/test_deny_fd_v2_boundary.py|pure/authority/old-source 경계|
|13|docs/evidence/deny_fd_v2_schema.json|새 wire semantic schema|
|14|docs/evidence/deny_fd_v2_sources.json|사전 source manifest,자기 파일 제외|
|15|docs/deny_fd_v2_contract.md|새 계약과 제한|
|16|docs/deny_fd_v2_result.md|실제 관측한 구현/검증 결과|
|17|docs/superpowers/specs/2026-11-01-deny-fd-v2-producer-design.md|producer+이 scope 설계를 합친 승인 spec|
|18|docs/superpowers/plans/2026-11-01-deny-fd-v2-source.md|승인 후 작성할 실행 plan|

별도 scope-spec/review JSON/fixture/build-artifact/capture/runner를 추가하지 않는다.
synthetic wire fixture는 두 신규 test 파일 안에서 만든다. 실제 build 로그/ELF/
post-build manifest는 소유한 외부 scratch에 두며 실제 guest acquisition harness는
이18개에 포함하지 않는다. 더 큰 구현이 필요하면 새 승인 없이 경로를 늘리지 않는다.

39개 preserved 경로와 현재 B의 mode/blob/SHA-256 전체 목록은 같은 폴더의
exact-path-scope-proposal.json에 있다. 이 draft는 future_P3/postimage=null이고
실제 policy manifest와 다른 schema를 가진다. 코드가 authority로 읽어서는 안 된다.

이 scope의 `tests/deny_fd_v2/`는 직전 producer 문서의 제안 위치
`tests/experiments/deny_fd_v2/`를 경로에 한해 대체한다. wire/lifecycle/권한 경계는
바꾸지 않는다. 세 기존 guard가 tests/experiments의 모든 추가를 원래22개
closed-exception 검사에 직접 전달하므로 그 위치에서는 hook에 도달할 수 없다.
기존 experiments/guard/query는 수정하지 않고,새 standalone test package 경로를
정확히 승인 목록에 노출한다. 상위 policy의 전체58경로 검사는 모든 새 파일에
계속 적용되므로 directory 이동으로 전역 검사를 우회하지 않는다.

기존 loader preimage:mode100644,
blob b4c95217b1942dc0110ecf4ddb9e4fc7b6851b63,
SHA256 00704f7b984af67e2f3270a90e03f08b69a555c6b6ba0d188ffad6aff36b5616.

## 4. 고정 history cohort와 fail-closed 선택

기존 loader는 원래 순서대로 P/P2 lineage와29개 frozen 상태를 모두 검사한 다음
새 helper를 호출한다. 따라서 기존 test가 기대하는 실패를 새 hook이 먼저 가리지 않는다.
새 helper는 stdlib만 사용하고 기존 loader를 역으로 import하지 않는다(circular import 금지).
module import 단계에는 Git/IO를 실행하지 않는다.

cohort는 branch 이름/working manifest 존재 여부/env/caller flag로 선택하지 않는다.
읽기 전용 `git merge-base --is-ancestor B HEAD`의 정확한 exit code를 사용한다.
Git unavailable/missing object/timeout을 역사 코호트로 간주하지 않는다.

| B ancestor HEAD 결과 | 의미 | helper 결과 |
|---|---|---|
|0|B를 포함하는 현재/새 코호트|P3 필수;모든 검증 뒤 신규18개 반환|
|1|P2이후이지만 B를 포함하지 않는 역사 코호트|신규 허용 없음,empty 반환|
|그 외/예외|Git/object 판정 불가|REJECTED;fetch/fallback 없음|

P2 ancestor HEAD와 원래29개 검사는 이미 상위 loader에서 필수로 실행한다.
source B와 HEAD가 실제 commit object인지도 확인한다. ancestor의1만 정상적인
negative이며 CalledProcessError를 넓게 catch해서 false로 바꾸지 않는다.
`GIT_NO_LAZY_FETCH=1`,`GIT_NO_REPLACE_OBJECTS=1`,`GIT_OPTIONAL_LOCKS=0`,bounded timeout을 유지한다.

P2 fixture checkout 또는 그 아래의 mutation commit은 B descendant가 아니므로
기존40개 scope만 적용된다. 이는 새 코호트에서 P3가 없을 때의 fallback이 아니다.
HEAD=B만 되어도 P3 필수이며 P3 부재를 무시하지 않는다. B 이전으로 HEAD를
옮기고 신규 파일을 index/worktree에 남기는 경우에도 상위 scope40검사가 거부한다.
역사 코호트는 신규18개를 절대로 반환하지 않는다.

기존 P2 fixture는 current Python validator가 명시적으로 historical Git root를
검사하는 기존 방식 그대로다. 원본1c4/cfc31c의 역사 실행은 기존 isolated child와
complete verified snapshot을 그대로 사용하며 current source를 overlay하지 않는다.

## 5. P3 사전등록과 순환 해소

미래 승인된 새 로컬 branch는 B에서 시작한다. 권장명은
`feat/deny-fd-v2-source-contract`다. 기존 PR54 branch를 움직이지 않는다.

P3는 B를 유일한 parent로 가지는 첫 append-only commit으로 고정한다.
사전에 RED 테스트를 쓰고 실행한 뒤,기존 loader의 최종 hook postimage를 완성한다.
P3에는 그1개와 manifest/spec/plan/작성된 신규 history test 같은 허용 파일만 넣는다.
새 helper 파일은 P3 이후에 추가한다. 따라서 기존 loader는 P3 literal을 갖지 않고,
P3 manifest는 자기 commit hash나 새 helper의 자기 hash를 요구하지 않는다.
P3 직후에는 import가 아직 없는 helper를 참조하여 RED일 수 있으며 중간 tip을
게시/성공 결과로 보고하지 않는다. pinning 이후 enabled tip만 최종 검증한다.

실제 P3 manifest는 대략 다음 의미의 닫힌 schema를 가진다.

- schema:deny-fd-v2-history-successor-v1;source_base=B;prior_P/prior_P2 exact pins.
- preserved:39개 exact path/image(mode/blobSHA1/SHA256), B와P3에서 같은 값.
- modified:정확히 기존 loader1개의 B preimage/P3 postimage와 mode.
- new_paths:정확히 표의18개;39+1+18=58,delta19.
- digest_meaning:CONTENT_IDENTITY_ONLY_NOT_AUTHENTICITY_OR_AUTHORITY.
- runtime_qualified=false;기존9개 operational permissions 모두false.

P3 SHA는 P3 후 작성하는 신규 helper의 고정 constant로만 pin한다.
P3 manifest 내 P3 SHA는 넣지 않는다. 미래 SHA/postimage는 지금 draft의null을
성공 값으로 간주하지 않고 실제 bytes/commit 생성 후 계산한다.
P3 parent=B, P/P2→B→P3→HEAD lineage,local blob 존재를 모두 검사한다.
manifest를 working/index 파일에서 읽지 않고 P3의 Git object에서 읽는다.
중복 JSON key/경로,추가 field,wrong type/flags/counts를 거부한다.

현재40개 path set은 immutable P의22files+7new 및 P2의11new의 union으로 검증한다.
working manifest에서 path set을 만들지 않는다. 신규18개는 새 helper에도 닫힌
상수 집합으로 명시하며 manifest가 새로운 path를 스스로 허용할 수 없다.

## 6. enabled current-cohort 검증

1. 기존 loader의29개 검증은 변경 없이 먼저 통과해야 한다.
2. 새 helper는 B/P3의 원시 blobs/modes를 읽어39preserved와1modified metadata를 검증한다.
   git archive/checkout 변환 bytes를 raw blob 대신 쓰지 않는다.
3. HEAD/index/worktree에서39개는 B image,modified1개는 P3 postimage여야 한다.
   unmerged index는 신규 경로에서도 거부한다. symlink/삭제/rename/exec mode도 거부한다.
4. bytes가 다르면 CRLF→LF만으로 정확히 frozen bytes가 되고 실제 Git-clean hash도
   같은 경우만 기존 기준대로 허용한다. arbitrary filter/strip/hash 완화는 없다.
5. B 대비HEAD/index/worktree/untracked delta는 modified1+new18의 subset이어야 한다.
   기존 상위 policy의 원래 BASE 대비58개 scope검사도 그대로 실행한다.
6. 성공 뒤에만 신규18개를 반환한다. 결과는 파일 검증 범위일 뿐 실행 권한이 아니다.

P3 manifest의 working copy 변경은 policy metadata를 바꾸지 못한다. 이 파일은
신규18개 중 하나여서 이번 phase의 self-authentication 대상은 아니며 final head
review에 의존한다. 반면 옛 P2 manifest는 이제39preserved의 하나여서 새 코호트에서는
working bytes 변경도 거부한다. 기존 P2 fixture의 허용 테스트는 역사 코호트에서
원래대로 실행하고,현재 코호트의 더 강한 보존 기준은 새 test에 추가한다.

기존 loader의 hook을 포함한 postimage는 P3 후 변경하지 않는다. 변경이 필요하면
동일 scope라는 이유로 수정하지 말고 사전등록 설계/권한을 다시 검토한다.
새 helper/18개 파일은 코드 review의 대상이며 자기 hash를 승인/보안 경계로 주장하지 않는다.
임의의 hostile Python/Git config 환경에 대한 adversarial sandbox는 제공하지 않는다.

## 7. partial P3와 최종 scope의 구분

P3 fixture는 enable/source 구현 이전의 partial commit을 검사할 수 있다.
따라서 helper의 역할은18개의 allowed set을 검증하는 것이지 모든 신규 파일이
이미 구현됐다는 선언이 아니다. 최종 완료 전 새 architecture test가 실제 current
HEAD delta를 modified1+new18과 정확히 비교해19개 전부 존재함을 별도로 보장한다.
누락 파일/extra 경로로 완료할 수 없고,이 최종 검사를 skip하지 않는다.
중간 partial commit의 metadata 검증 성공을 전체 구현 GREEN으로 보고하지 않는다.

producer source commit M은 P3 이후 별도로 고정한다. pre-build source manifest는
M의 고정 source 파일만 기록하며 자신의 파일/ELF/final capture를 포함하지 않는다.
M 이후 source manifest/result 기록 commit을 추가하고 source-bound compile-only를
검증한다. P3 hash와 producer source/build/capture hash는 각각 다른 식별자다.
정확한 compile helper/새 wire 동작은 직전 producer 설계를 따른다.

## 8. 필수 실제 Git 검증

기존 tests/test_history_transition_policy.py와18개 기존 guards는 수정하지 않는다.
기존 node IDs/assertions/P/P2/fixture checkout/isolated historical runner 그대로 실행한다.
추가 검사는 새 tests/test_deny_fd_v2_history_policy.py에만 둔다.

- P2와 P2 기반 mutant HEAD에서 old scope40 유지,신규18개 반환 없음.
- B의 완전한 원본 source를 별도 고정 clone/isolated child에서 실행하면 기존
  등록-transition node가 그대로 통과함을 확인한다. current validator로 B를
  검사할 때 P3를 요구하는 것과 옛 source 자체의 역사 동작을 구분한다.
- exit1 vs missing B/HEAD/object/timeout을 구분;error를 historical false로 처리하지 않음.
- 현재 B/P3 descendant는 missing/wrong P3,parent/lineage/manifest를 거부하며 fallback 없음.
- P/P2 immutable metadata와 original22/P2 two postimages 보존 확인.
-39preserved 각각 실제 HEAD/index/worktree byte/mode/delete/rename 변경 거부.
- modified loader의 실제3layer×4mutation 거부;worktree 복구로 index/HEAD 은폐 불가.
- P2 working manifest는 old fixture에서 원래 허용,current P3에서 보존 실패.
- P3 working manifest 변경이 pinned policy를 바꾸지 못함;fake new path/false→true도 안 됨.
- 같은 directory의 unlisted 파일,old scope 외 source/CI/fixture 변경,unmerged/symlink 거부.
- actual Git CRLF false/true와 추가 content drift;Windows에서도 skip 없는 동등 검사.
- HEAD를 역사 시점으로 옮기고 신규 파일을 index/worktree에 남긴 downgrade 거부.
- 최종19delta/58cumulative 정확한 file set,39preserved/1postimage 고정.

새 body는 callback/mock 반환값만 비교하지 말고 소유한 temp Git clone에서 실행한다.
순수 permission/type/schema 판단은 별도 unit test로 해도 Git-layer 증거를 대신하지 않는다.
모든 파일39×3×4의 비용은 측정하고 clone fixture 재사용 최적화는 해도 검사 항목을 줄이지 않는다.
전체 pytest,source/history audits,ruff/format/mypy,coverage,build/fresh wheel/replay/
knowledge/owner/science smoke와 fresh exact-head 내부 review를 최종 gate로 둔다.
C/decoder compile-only와 synthetic tests를 guest/kernel/vehicle 증거로 바꾸지 않는다.

## 9. 다음 승인 범위와 비목표

제안하는 다음 작업은 위19개 delta 안에서만 로컬 source-first 구현/검증이다.
사용자가 이 문서 scope를 승인하면 writing-plans를 먼저 사용하여 plan을 작성한다.
새 helper/decoder/C를 지금 만들거나 승인 전에 scaffold/compile하지 않는다.

승인 범위에도 PR 게시/ready/merge/rebase/force push,기존 PR/main 변경,
guest/QEMU/kernel/device/vehicle/host ELF 실행,새 actual capture,임의 command/payload,
Params/controller/cereal/runtime schema 변경,estimator/qualification/application/owner
bridge,external AI/longitudinal/upstream PR은 포함하지 않는다. source C는 build할 수
있지만 host에서 실행하지 않으며 source compile만으로 operational permission을 얻지 않는다.

DENY_FD_V2_HISTORY_SCOPE_DESIGN_READY는 설계 상태다.
HISTORY_SUCCESSOR_SCOPE_APPROVAL_PENDING/PRODUCER_NOT_IMPLEMENTED/
OBSERVED_V2_CAPTURE_UNAVAILABLE/LEGACY_PR34_M1_OPEN/
FD_OFD_LIFETIME_OBSERVER_UNQUALIFIED/APPLICATION_NOT_AUTHORIZED를 유지한다.
기존 나머지 runtime/vehicle/empirical/watchdog/executor blockers와9false도 유지한다.

## 10. Builder check와 작성자 확인

fresh builder check는 위 experiments 경로의 pre-hook 거부 문제1건을 질문했다.
원인을 기존 policy175와3개 guard에서 확인하고,별도 tests/deny_fd_v2 경로로
6개 제안 파일만 옮겼다. 사용자 승인 전 제안서의 위치 수정이며 저장소 파일을
이동하거나 추가한 것이 아니다. 기존1+신규18,delta19/누적58은 변하지 않는다.

실제 기존 assert_history_transition에 옛 prefix를 넘겨 pre-check 거부를 재현했다.
18개 guard의 실제 Git baseline diff에 가상 추가 path set을 넣는 read-only 진단에서
옛 prefix는3개 guard가 거부했고 새 prefix는18개 모두 사전 검사를 막지 않았다.
결과는 path-routing-diagnostic.json에 있다. 첫 보조 진단은 모든 Git diff가 `--`를
쓴다고 잘못 가정해 assertion이 났고,full-tree query도 처리하도록 진단만 수정했다.

이 진단은 P3 구현/실제 Git mutation test를 대신하지 않는다. 기존193개
history/architecture baseline은 통과했고40개 preimage hash를 검증했다.
작성자가 builder 질문에 답해 설계를 고친 것이며 독립 clean 재검토나 C/I/M 코드
리뷰를 받았다고 주장하지 않는다. 실제 구현 전에 사용자 exact-path 승인이 필요하다.
