# ADR-F1: Admission fence와 원본 D custody

**Status: PROPOSED — DESIGN ONLY**  
Date: 2026-11-05  
Base: 694604e0722373d6666600e202e454b79a9d3d02  
설계 선택: 위임된 연구 설계 결정. OS 정책 채택·설정·실행 승인이 아니다.

## 1. 결정

**D 생성 전부터 최종 제거·handle release까지 OS-enforced exclusive-authority 경계를 유지한다.**
snapshot/kcmp/nonce/세대는 그 경계의 consistency check로 남기며 fence 자체라고 부르지 않는다.
현재 UID1000 기반 프로토타입에는 이 강한 집행 경계의 binding이 없다.
따라서 trusted-single-owner lab PASS를 강한 fenced execution으로 승격하지 않는다.

후속 구조는 **보호된 host principal/동등한 강제 정책 + 신뢰된 factory + E 전용 parent P**다.
다른 host UID는 가능한 수단이며 충분조건은 아니다. 같은 UID도 검증된 LSM 정책으로 분리할 수 있으나
현재 그런 정책은 확인·설정하지 않았다. 관리자/설정 변경이 필요한 backend는 별도 승인 경계다.

이는 현재 노트북에 공격자가 있다는 관측이나 모든 Linux 구성의 불가능성 증명이 아니다.
현재 source·인계·허용 권한에서 요구하는 외부-writer 배제 근거가 없다는 판단이다.

## 2. 역할과 위협 모델

- F: 신뢰된 factory/정책 집행 주체. 새 외부 P의 원래 authority를 보유한다.
- E: 검토된 native owner. P를 빌리되 내부 D는 직접 생성하고 원본 refs를 유지한다.
- W: 최초 profile의 고정 합성 bootstrap/worker 하나. 임의 payload/fork tree는 제외한다.
- X: 신뢰 경계 밖 actor. 경로나 과거 receipt를 알아도 된다.
  **OS 권한이 있다면** 이름·membership·subtree·control·code·FD를 변경하려 한다.
- Kernel/정책 집행/호스트 관리자는 TCB. root/관리자 또는 TCB 침해 방어는 주장하지 않는다.

같은 UID라는 이유만으로 모든 actor에게 모든 mutation 권한이 있다고 가정하지 않는다.
요구하는 위협 모델은 권한을 가진 X를 배제하는 증거가 필요하다는 것이다.
namespace·UID·과거 metadata를 현재 authority로 전이하지 않는다.

목표는 E가 검사한 뒤 X가 바꿔 원치 않는 group kill/remove가 일어나지 않게 하는 것이다.
비목표는 실제 provider/H/차량, qualification16 충족, namespace containment·readonly mount·
외부 writer/async drain·crash recovery의 구현이다. 이번에 권한/설정을 바꾸거나 OS 실험을 하지 않는다.

## 3. Source에서 확인한 공백

base694604e의 src/native_e_lab/domain_supervisor.c 기준.

| 위치 | 현재 동작 | 부족한 부분 |
| --- | --- | --- |
| L40–71 | factory 형태/parent UID/type | metadata는 exclusive writer 보장이 아님 |
| L245–249 | mkdir 뒤 open/dup/kcmp | 최초 mkdir 객체와 나중 연 객체 사이 교체 가능성 |
| L73–83 | 현재 D FD/anchor/name 일치 | 서로 일치해도 최초 생성 객체라는 증명은 아님 |
| L271–281 | child/image/FD/members/subtree snapshot | 검사 직후 변경 차단 없음 |
| L283–290 | 원본 D FD에 kill | 같은 D에 뒤늦게 들어온 미소유 task도 영향 가능 |
| L296–300 | name 확인 뒤 unlinkat | name 확인과 제거가 별도 연산 |
| L303–320 | UNKNOWN 유지·원본 pidfd fallback | 피해 제한이며 외부 권한 회수/fence는 아님 |

아래는 source-level 반례다. 이번에 실제 actor 공격을 실행한 결과가 아니다.

**A — 생성 객체:** E가 빈 D0를 mkdir → 권한 있는 X가 D0 제거/같은 이름에 D1 생성 →
E가 D1 open/dup/kcmp → 현재 비교는 모두 맞아도 최초 D0의 original custody는 증명되지 않는다.

**B — admission/stop:** E가 worker1개·descendants0 확인 → X가 자기 synthetic task/subtree를 넣음 →
E가 올바른 D FD로 kill → 객체 identity는 맞아도 미등록 task에 영향이 생긴다.
kernel kill 동작 내부의 migration 보호를 user-space 사전 검사 구간 전체의 fence로 해석하지 않는다.

**C — 제거:** D가 빈 상태에서 E의 name 검사 통과 → X가 D0 제거/같은 leaf에 D1 생성 →
E의 unlinkat(P,name)이 D1에 작용할 수 있다. 원본 FD 보유와 name-based 조건부 제거는 다르다.

## 4. 인터페이스 근거와 설계 추론

cgroup.kill은 subtree에 적용되고, frozen 상태에서도 task 이동/tree 연산이 가능하다.
따라서 freeze를 외부 admission·이름 변경의 완전한 배제로 쓰지 않는 것은 이 인터페이스에 근거한 추론이다.
[Kernel cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html).

unlinkat은 dirfd 기준 이름을 해석하며 AT_REMOVEDIR로 directory 제거를 선택한다.
원본 inode 비교와 제거를 합친 API라고 해석하지 않는다.
[unlinkat(2)](https://man7.org/linux/man-pages/man2/unlinkat.2.html).

owner의 mode 변경 권한 때문에, owner와 같은 host 권한의 X에게 일시 chmod만으로 배제를 입증할 수 없다.
실제 cgroup별 권한 집행은 별도 검증 대상이다.
[chmod(2)](https://man7.org/linux/man-pages/man2/chmod.2.html).

FD와 open-file-description은 구분한다. retained FD가 다른 actor의 권한을 회수하는 장치는 아니다.
[open(2)](https://man7.org/linux/man-pages/man2/open.2.html).
user namespace의 UID0을 별도 host owner identity로 승격하지 않는다.
[User namespaces](https://man7.org/linux/man-pages/man7/user_namespaces.7.html).
Landlock을 적용 대상 process 밖의 모든 기존 actor에 대한 강제로 대체하지 않는다.
[Landlock](https://docs.kernel.org/userspace-api/landlock.html).

공개 systemd255 resource-control 문서 조회는 timeout이었다. 읽거나 현재 정책을 검증한 근거로 사용하지 않는다.

## 5. 선택지와 결정 이유

| 선택지 | 효과 | 남는 공백 / 결정 |
| --- | --- | --- |
| snapshot 반복/kcmp/nonce/generation | 변화 발견·correlation | 검사 사이 mutation, fence로 불가 |
| advisory lock/cooperative broker | 협력 actor 순서화 | raw OS writer가 우회, trusted lab 한정 |
| chmod/불규칙 이름 | 일부 접근 제한/충돌 회피 | owner/기존 alias/권한 있는 X, 단독 불가 |
| freeze/max-descendants/worker view RO | 각 기능의 제한된 효과 | external admission/name/code 권한 전체 배제 아님 |
| worker-only seccomp/Landlock | 적용 worker 행동 제한 | 기존 외부 actor는 남음 |
| namespace 또는 namespace UID0만 사용 | 가시성/namespace별 권한 변화 | host authority 격리와 동치 아님 |
| OS-exclusive authority + F + E-only P | 원인인 mutation 권한을 배제할 수 있는 구조 | 실제 집행/지속성/잔존 rights 증명 필요, **선택한 전제** |

추가 운영·증명 부담을 감수한다. 현재 소프트웨어를 이름만 fenced로 바꾸는 선택은 하지 않는다.
새 host principal 또는 LSM/manager 정책이 필요해도 이번에 설치·설정·권한 상승하지 않는다.

## 6. Fence contract F1 — 문서상 의무, 구현된 권한 객체 아님

I = [새 P 생성 직전, 모든 cohort resource의 확인된 retirement 완료].
interval 전체에 다음을 요구한다.

1. P는 이번 F가 만든 새 scope. 기존 path/FD/receipt로 채택하지 않는다.
2. X의 P/D 이름·membership·subtree·limits/kill mutation authority를 배제한다.
3. X의 E/F process memory·FD table·code/manifest 변경도 배제한다.
4. 기존 writable FD, inheritance, SCM_RIGHTS/proc 등 alias 유출까지 포함한다.
5. 신뢰 manager/F도 계약 밖 task를 D에 넣거나 이름을 바꾸지 않는다.
6. F가 만든 D를 전달해 E-created라고 부르지 않는다. **E가 D를 직접 생성**한다.
7. E는 D 밖에 있고 admission 경로는 고정된 하나다.
8. W가 untrusted로 바뀌면 E와 같은 mutation 권한을 남길 수 없다.
   현재 trusted worker의 결과를 미래 임의 payload로 확장하지 않는다.
9. fence/original identity 불확실성은 terminal. 나중 snapshot/receipt로 해제하지 않는다.
10. broker 종료/timeout/expiry가 배제를 풀거나 host principal을 재사용하게 해서는 안 된다.
11. in-flight syscall/live alias/task/외부 writer가 불확실하면 retire하지 않고 quarantine한다.
12. 이 의무를 true로 채운 JSON/class/hash/세대가 실제 집행이나 실행 authority는 아니다.

F1은 기존 qualification16의 새 버전이나 provider 등록 레코드가 아니다.
현재 실제 F1 집행/host binding은 UNAVAILABLE/미구현이다.

## 7. 원본 live handoff

권한 사슬: F의 원본 P authority → E-only live parent grant → E의 mkdir(D) →
retained original D refs → 생성 syscall에서 얻은 child pidfd.

- ParentGrant는 외부 P만 의미한다. 가져온 D FD를 E-created로 재명명하지 않는다.
- 미래 public entry도 인자 없는 고정 synthetic factory다.
  generic command/path/PID/FD/unit/receipt/recover API를 제안하지 않는다.
- E-only 채널은 factory가 생성부터 보유한 원래 연결에 binding한다.
  같은 UID peer, socket path, nonce 또는 PID 숫자 하나를 신뢰 근거로 쓰지 않는다.
- backend가 parent FD 전달을 쓰면 worker bootstrap과 분리한 **내부 factory 전용** handoff다.
  origin·OS fence·정확한 FD 수/type를 검증하고 extras는 수신 refs만 한 번 닫는다.
  기존 worker의 unexpected-FD 거부를 완화하지 않는다.
- live grant는 직렬화/복구할 수 없다. receipt deserialize로 native guard를 만드는 API가 없다.
  class의 비직렬화만으로 hostile Python/OS 경계를 만든다고 주장하지 않는다.
- P의 배제는 D 생성 이전부터 유효하다. mkdir→open을 단일 syscall이라고 하지 않는다.
  외부 writer를 배제한 구간에서의 linearization을 요구한다.
- caller-writable binary/sidecar의 동일 hash, path 검사 뒤 재open, argv 이름은 origin 인증이 아니다.
  보호된 code store/원래 executable handle·loader/환경을 TCB 규약에 포함한다.
- worker image 진입 전에 host directory/control refs를 제거한다.
  이후 임의 FD import/fork/plugin 확장은 별도 설계·승인 없이는 불가다.

현재 Delegate=yes는 기능 관측일 뿐 이 handoff나 exclusive authority를 증명하지 않는다.

## 8. Lifecycle과 한 번만 시도하는 규약

아래는 설계 상태이며 실행 가능한 state machine이나 승인 모델을 이번에 구현하지 않았다.

| 상태 | 진입 조건 | 허용/금지 |
| --- | --- | --- |
| EMPTY | cohort 객체 없음 | F1 근거 없으면 P/D/worker 생성0 |
| PARENT_HELD | 새 P original grant + 지속적 OS fence | E가 D 단1회 생성 |
| CREATED_UNBOUND | mkdir 성공, D FD 미획득 | worker 금지; FD 획득 실패 시 이름으로 회수하지 않음 |
| D_BOUND | 보호된 구간의 원본 D refs | 고정 clone3 birth 한 번 |
| BORN_BOUND | 원본 pidfd, child 안/E 밖 | exec/FD 검증 전 RUN 금지 |
| ENTRY_READY | 고정 image·origin·bounded protocol 일치 | worker 하나만 RUN |
| SEALED | local admission closed + F1 지속 | snapshot은 consistency check |
| STOP_ATTEMPTED | original D authority/outside E/known registry | 시도를 syscall 전에 소비; D kill 한 번 |
| REAP_ATTEMPTED | 원본 pidfd | wait 한 번, 정확한 종료 종류 확인 |
| DRAINED | 등록 task 전부 회수 + 확인된 populated0 | 외부 writer/async drain은 별도 미충족 의무 |
| REMOVE_ATTEMPTED | 제거까지 지속되는 F1와 원본 P/D | unlink 한 번, 불명확 시 재시도 금지 |
| RETIRED | refs/results/in-flight/aliases 확정 | 그때만 scope/principal 재사용 검토 |
| AUTH_LOST/OWNERSHIP_UNKNOWN | fence/original binding 불명확 | terminal; group kill/unlink/reattach 금지 |

~~~mermaid
stateDiagram-v2
    EMPTY --> PARENT_HELD: independently enforced OS fence
    PARENT_HELD --> CREATED_UNBOUND: E mkdir
    CREATED_UNBOUND --> D_BOUND: original refs under same fence
    D_BOUND --> BORN_BOUND: clone3 and original pidfd
    BORN_BOUND --> ENTRY_READY: fixed exec and FD checks
    ENTRY_READY --> SEALED: one worker admitted
    SEALED --> STOP_ATTEMPTED: consume one-shot stop
    STOP_ATTEMPTED --> REAP_ATTEMPTED
    REAP_ATTEMPTED --> DRAINED: definite original-child reap
    DRAINED --> REMOVE_ATTEMPTED: fence still held
    REMOVE_ATTEMPTED --> RETIRED: definite removal and release
    CREATED_UNBOUND --> OWNERSHIP_UNKNOWN: original FD unavailable
    SEALED --> AUTH_LOST: fence continuity unproven
    STOP_ATTEMPTED --> OWNERSHIP_UNKNOWN: uncertain result
    REMOVE_ATTEMPTED --> OWNERSHIP_UNKNOWN: uncertain result
~~~

모든 live 상태에서 fence 상실은 terminal이다. diagram의 loss edge는 일부만 보인다.
전이 guard는 실제 authority/policy 의무이며 callback/record가 부여하지 않는다.

### Revocation
broker가 살아 있음을 조회하고 kill하는 방식은 새 check/use race를 만든다.
OS/manager의 배제는 channel/heartbeat 종료 뒤에도 임의 writer에게 열리지 않아야 한다.
revoke는 새 admission을 막을 수 있으나 in-flight/잔존 refs가 있는 동안 배제를 풀지 않는다.
expiry는 권한 확대·UID 재사용 이벤트가 아니다. 이를 구현 못하는 backend는 시작하지 않는다.

### 불확실 정리
D stop을 아직 시도하지 않았고 original child pidfd custody가 독립적으로 확정됐을 때만
이미 승인된 fixed-child fallback을 고려할 수 있다.
D kill UNKNOWN 뒤 pidfd/anchor/parent로 같은 child 정지를 다시 보내 완료시키지 않는다.
wait/close/unlink UNKNOWN도 다른 alias·PID·path로 우회 재시도하지 않는다.
사용하지 않은 별도 owned ref의 한 번 close와 불확실 operation 재시도는 구분한다.
원본 handle 없이는 lookup으로 복구하지 않는다.
manager의 독립 outer teardown은 E의 UNKNOWN을 CONFIRMED로 바꾸지 않는다.
b2f2d50의 이전 UNKNOWN에 이 설계를 소급 적용하지 않는다.

## 9. 미래 acceptance matrix — 이번 미실행

모든 actor와 target은 별도 승인된 새 synthetic cohort만 사용한다.
기존 service/cgroup/task/file 대상 공격은 금지한다.
invalid path/메시지 거부를 OS fence 증거로 세지 않는다.
actor가 자기 별도 fixture를 쓸 수 있는 positive control, 실제 credentials/namespace,
원래 target binding을 함께 확인해야 한다.

| ID | 시나리오 | 요구 결과 |
| --- | --- | --- |
| T01 | F1 누락·위조·미바인딩 | P/D/worker 생성0 |
| T02 | mkdir→open 사이 remove/replace | OS 거부; 허용되면 F1 실패/worker 금지 |
| T03 | snapshot 이후 task 주입 | OS 거부; 사후 감지만으로 PASS 불가 |
| T04 | 숨은 subgroup/손상 stat/새 subtree | admission/stop 거부, UNKNOWN 유지 |
| T05 | 확인→unlink 사이 교체 | OS 거부; 입증 못하면 unlink 금지 |
| T06 | 동일 UID/worker의 control 재open·chmod | 배제 증명 또는 backend UNSUPPORTED |
| T07 | 기존 writable alias/inherited FD/SCM_RIGHTS | leak 부재 입증, 사후 chmod만으로 PASS 금지 |
| T08 | code/manifest/exec·memory·FD 탈취 | OS 경계로 배제, hash만으로 PASS 불가 |
| T09 | disconnect/expiry/revoke vs stop | 새 동작 차단, 배제는 닫힌 채 유지, 재사용 금지 |
| T10 | partial/EINTR/wait/close/remove 불명확 | 한 번 시도, UNKNOWN, alias/parent 재시도 없음 |
| T11 | 위조·직렬화·replay·다른 cohort/세대 | 진단 일치 여부와 무관하게 live 권한 생성0 |
| T12 | extra/missing FD·빈/초과/부분 frame·EOF | 기존 bounded/received-ref 규칙 유지 |
| T13 | worker escape/self-move/fork | OS/TCB 규약으로 거부, 미지원이면 시작 금지 |
| T14 | outer 정리/PID 종료만 관측 | native UNKNOWN 해제·principal 재활용 금지 |
| T15 | 정상 fresh single-worker | E-created D/원본 refs/outside E/stop+drain+remove와 I 전체 증거 |

pure model/mock/regular-file fixture는 논리 회귀일 뿐이다.
실제 OS 거부·원본 custody·F1 지속성의 성공으로 세지 않는다.
이 표는 현재 실행한 테스트나 새 qualification evidence가 아니다.

## 10. 후속 구현 계획 — 이번 구현 없음

1. **집행 backend와 별도 권한 경계를 검토한다.**
   host principal/LSM/manager, code store, original handoff, quarantine의 집행 주체·수명을 구체화한다.
   관리자 변경이 필요하면 이유·정확한 변경안·rollback/검증을 별도 승인 대상으로 만든다.
2. **별도 후속 연구 branch에서 구현한다.**
   책임 단위는 native fence backend / parent handoff / E lifecycle / adversarial harness다.
   파일·ABI는 backend 확정 뒤 정하며, boolean placeholder provider를 만들지 않는다.
3. **TDD·source review로 T01–T14를 구현한다.**
   기존178개와 제품 guard/thresholds를 보존한다. 실패 주입은 tests에만 둔다.
4. **독립적으로 범위/권한이 충족된 경우만 새 lab을 허용한다.**
   fixed worker, 기존30s/5s/128MiB/no-swap/8tasks/25% caps, 새 unit1개만 활성화.
   F1 미확인 시 worker0. 외부 P를 E-created D로 바꾸어 부르지 않는다.
5. **회귀·독립 리뷰·원래 handle 정리·구분된 보고를 한다.**
   mock/OS/source revision/미실행을 나눈다. 기존14false·UNBOUND·16UNAVAILABLE를 유지한다.

## 11. 결과와 승인 경계

설계는 더 많은 snapshot으로 gap을 덮지 않는 선택을 한다.
현재 자료로 이 노트북의 강한 OS fence 실행 가능성을 PASS하지 않는다.
새 host authority/정책을 실제로 마련하는 것은 이번 범위가 아니며 자동 실행하지 않는다.
Proposed 문서는 policy_adopted/runtime_accepted/runtime_qualified를 true로 만들지 않는다.
실제 H/provider/차량 payload, qualification16, 과거 UNKNOWN은 그대로다.
