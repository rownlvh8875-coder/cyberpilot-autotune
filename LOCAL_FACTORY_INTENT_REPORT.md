# LOCAL NATIVE E — native factory intent 연구 후속 구현

STATUS: PASS_NATIVE_FACTORY_INTENT_WITH_RELEASE_LIMITATION
Date:2026-11-06
Base:d24cb17ef9e557286f8555680a033518529d10a4
Branch:research/native-e-factory-intent
최종 commit/CLEAN 상태는 외부 FINAL_DELIVERY.json에 기록한다.

manager 요청 전 **실제 O_EXCL 파일 생성·단일 write·file/root fsync·원본 FD 검사**를 연결했다.
동시 factory, 재실행, crash, 부분 쓰기와 불확실한 syscall 결과를 제한된 private fixture로 검증했다.
기존 환경 조회나 approval boolean을 추가하는 작업이 아니다.

이는 native E 전체나 protected F1 구현 완료가 아닌 연구 component다.
실제 관리자 계정·권한·서비스·code store를 만들지 않았고 새로운 systemd unit/cgroup도 실행하지 않았다.

## 코드와 실행 순서

| 파일 | 역할 |
| --- | --- |
| research/factory_intent/intent.c | 원본 scope/file OFD, intent O_EXCL/fsync/readback, fail-closed 처리 |
| research/factory_intent/internal.h | 숨겨진 component 내부 live 타입; 제품 provider API 아님 |
| research/factory_intent/factory.c | fi_run_fixed(void), intent 이후에만 기존 fm_run_fixed 한 번 호출 |
| research/factory_intent/unbound.c | 기본 scope는 ENOSYS; host path·bus fallback 없음 |
| tests/native/factory_intent_driver.c | fresh fixture만 여는 constructor 및 테스트 전용 실패 주입 |
| tests/test_factory_intent.py | 61개 회귀, 두 native binary strict build |
| FACTORY_INTENT_DESIGN.md / FACTORY_INTENT_REVIEW.md | 계약·한계·독립 리뷰·수정 기록 |

외부 실행 API는 fi_run_fixed(void)뿐이다.
caller가 path/PID/FD/unit/command/receipt를 넘기는 실행·복구 API는 없다.
기본 binary는 scope0/intent0/Start0/E0이며 추가 CLI 인수도 거부한다.
별도 test constructor만 새 private state directory를 연다.

실행 순서:

1. process 내 one-shot을 constructor 전에 소비한다.
2. 원본 parent/root FD와 OFD anchor, 고정 state name, owner/mode를 검사한다.
3. 새 nonce·checked monotonic timestamp로 고정64-byte record를 준비한다.
4. attempt.intent를 O_EXCL/O_NOFOLLOW로 만든다. 기존 내용은 읽거나 해석하지 않고 DENY한다.
5. 단일 write/readback → file fsync → root fsync → 원본/name/content 재검사.
6. precondition이 성립할 때만 기존 고정 private synthetic manager 경로를 한 번 호출한다.
7. 최종 guard 후 primary refs만 소비·close하고 마지막 anchor slots는 terminal process 상태에 보존한다.

기존 manager가 E probe를 생성·원래 pidfd로 wait하며, F는 E pidfd를 채택하지 않는다.
그 manager는 실제 systemd가 아니다. wire 요청의 UID/cap/resource 설정도 적용하지 않는다.
새 component는 W를 실행하지 않는다.
intent/root FD는 SCM_RIGHTS 전달 대상이 아니다.
기존 M/E의 close_range 직후 상속된 intent/root FD가 닫혔는지 테스트 hook이 검사했다.

## 실제 fixture 관측과 negative 검사

| 경우 | 관측 |
| --- | --- |
| 정상 fixed factory | intent fsync 뒤 Start1, native private protocol 완료 |
| 새 process로 같은 state 재실행 | DENIED_EXISTING_INTENT, manager0, bytes 보존 |
| 동시에 factory2개 | 정확히 한 승자, 합산 Start1; 다른 실행 DENY |
| intent 생성 직후 / fsync 직후 crash | 새 직접 자식의 원래 Popen handle만 SIGKILL; 새 process는 DENY |
| 빈·손상·위조 성공 receipt·symlink·directory·FIFO·hardlink leaf | 기존 leaf를 해석·채택하지 않고 DENY |
| partial/zero/error/unknown write, read, file/root fsync | manager0, 동일 동작 재시도 없음 |
| clock/random 실패 또는 malformed/short 값 | intent 또는 manager 생성 전 거부 |
| leaf/root name·mode·link·content 변경 | guard 실패, 성공으로 승격하지 않음 |
| directory/file/socket FD 번호 재사용, 같은 inode의 다른 OFD | foreign FD 닫지 않음 |
| partial constructor/anchor 상실 | UNKNOWN/retained residue, inode-only close 없음 |
| manager 오류/최종 tamper/close unknown | 전체 완료 거부, intent 유지, 다음 process DENY |
| 두 번째 같은 process 요청 | constructor 재호출 없이 ALREADY_ATTEMPTED |

이 표의 파일·프로세스는 새 전용 fixture뿐이다.
negative hook이 일부 새 fixture 이름/내용을 바꾸거나 제거하는 것과
production intent 구현에 삭제·reset 기능이 있다는 주장은 구분한다.
production에는 unlink/recovery/reset/adoption 경로가 없다.
SIGKILL crash 실험은 신규 직접 자식에만 수행했으며 user-manager/WSL/기존 서비스는 종료하지 않았다.
전원 장애나 저장장치 내구성 실험은 아니다.

## release 제한과 리뷰 수정

독립 source reviewer가 Important1을 발견했다.
primary close 뒤 anchor를 inode/type만 대조하면, primary close가 success여도
같은 inode의 다른 OFD로 교체된 foreign anchor를 잘못 닫을 수 있었다.
leaf/root 두 사례를 RED로 재현한 뒤 수정했다.

수정된 구현은 pair 검사 뒤 primary만 소비/close한다.
마지막 anchor 슬롯은 comparator가 없으므로 다시 닫거나 사용하지 않는다.
static terminal context가 프로세스 종료까지 보존하며 다음 호출은 one-shot에서 차단한다.

**native_release=PARTIAL_REFS_RETAINED는 전체 cleanup PASS가 아니다.**
UNKNOWN close는 여전히 UNKNOWN이다.
프로세스 종료의 kernel FD 회수와 library close/외부 async drain 성공도 다른 사실이다.
해당 FD 잔여를 숨기지 않고 bounded research 실행의 의도적 비용으로 남겼다.

Reviewer가 실행하지 않은 것은 build/test/OS 실험이며 실제 실행 결과와 분리했다.
최종 repair 및 fortified-read test hook은 author 검증이다.
추가 author RED6으로 unknown/uninspected durability를 false 대신 null로 보존했고,
시험용 pause child의 무한 대기 RED를 재현해 고정 alarm4로 제한했다.
새 직접 자식은 harness 유실 때도 종료하며, 이 테스트 전용 변경을 최종61개에서 확인했다.
전체646 실행에는 기존586+신규60이 포함됐고, 추가된 bounded-pause1개를 포함한 최종61 subset을 따로 검증했다.
합계647은 node ID 중복을 제거한 수치이며 단일 pytest647 실행이라고 표현하지 않는다.
독립 post-fix C0/I0나 전체 보안 인증은 주장하지 않는다. material Minor는 없었다.

## 실제 환경과 검증 결과

새 실행에서 관측한 값: Ubuntu-24.04 WSL2,
Linux6.18.33.2-microsoft-standard-WSL2/x86_64, EUID/GID1000, CapEff0.
systemd/위임 metadata 전체 조사를 반복하지 않았다.
이전 WSL 호출과 같은 manager 세대라고 가정하지 않는다.
이번에는 새 unit/cgroup, user-manager 제어, sudo/설치/권한 상승이 전혀 없다.

| 검증 | 결과 |
| --- | --- |
| 전체 CPU/POSIX research regression | **647 unique PASS /0FAIL/0SKIP** = 기존586 + 신규61 (전체646 + 최종집중61에서60개 중복 제거) |
| 신규 focused suite | 61 PASS |
| UBSan focused | 61 PASS; 같은 사례 반복이며 합계에 더하지 않음 |
| GCOV focused | 61 PASS; 같은 사례 반복 |
| 새 intent.c | line70/70=100%, branch outcomes115/154=74.68% |
| 새 factory.c | line17/17=100%, branch outcomes34/38=89.47% |
| 기존 Python coverage | 91.74%, unchanged threshold90 유지 |
| Native compiler | -std=c11 -O2 -Wall -Wextra -Werror, exit0 |
| Ruff / format | exit0 /exit0, 76 Python files |
| mypy | 기존14 modules exit0; new C는 compiler 검사, Python tests는 Ruff 범위 |
| 기존 package/product build | NOT_RERUN_UNCHANGED |
| 기존 product2786PASS | 역사 결과이며 이번 합계에 포함하지 않음 |
| old123 non-ledger files / old refs | byte/hash 및 ref 보존 |
| remote push / merge / PR | NONE |

GCOV는 이번 fixture binary의 intent.c/factory.c만 보고한다.
SDK/kernel/M/E의 _exit 경로/default-unbound binary/과거 C coverage를 합쳐 인증하지 않는다.
branch outcome이 모두 실행됐다는 뜻도 아니다.
최초 UBSan51PASS/2FAIL은 fortification이 pread hook을 __pread_chk로 우회한
테스트 계측 문제였다. nm/local header 확인 후 checked 함수를 유지한 test-only hook을 추가했다.
fortification·검사 기준·기존 테스트를 낮추지 않았다. 최초 실패 로그를 보존했다.

## F1 및 실제 HOST에 남은 경계

이 latch는 **marker가 보존되는 trusted single-writer fixture의 중복 억제**를 검증한다.
악성 sameUID writer는 현재 private root를 변경할 수 있으므로 전체 admission fence가 아니다.
name/검사/manager 요청 사이의 exclusive writer 차단을 증명하지 않는다.

미구현/미검증:

- root-protected F/code/loader/state, 실제 account allocator와 E/W cross-UID credential seal.
- 실제 system bus의 동적 owner/job 및 원래 manager 생성 lifecycle/P binding.
- P 생성 전부터 retire까지 외부 name/membership/code/control/alias writer 차단.
- 실제 protected F1/original custody, readonly mount, namespace containment, arbitrary async drain.
- 자격 승인·제품 provider 등록·차량 readiness.

관리자가 만든 P를 E-created D라고 부르지 않는다.
기존 real-cgroup lab의 kernel D 성공도 이 새 component의 protected origin 증명으로 전이하지 않는다.
기존 ADR-A2 B01–B10과 과거16 qualification evidence는 계속 차단/UNAVAILABLE다.
같은 state에 intent가 남으면 자동 삭제·재시도·다른 이름으로 retarget하지 않는다.
현재 binary를 관리자 서비스로 설치하지 않는다.

provider_registration=UNBOUND.
qualification_required=16, available=0, status=UNAVAILABLE.
다음14개 모두false 유지:

application_authorized, build_execution_allowed, candidate_generation_allowed,
device_class_qualified, owner_proposal_allowed, policy_adopted, promotion_authorized,
runtime_accepted, runtime_qualified, actual_payload_released, cleanup_allowed,
recovery_execution_authorized, H_executed, HREQ004_qualified.

명시적으로 허용된 synthetic lab과 프로젝트의 제품 admission flag는 별개다.
실제 H/제품/차량 payload는 실행하지 않았다.
기존 사용자 파일/작업 트리/이전 evidence/Carrot/Jetson/Params는 변경하지 않았다.

## 재실행과 인계

```text
.venv/bin/python -m pytest -q tests/test_factory_intent.py --basetemp=<new-private-path>
FI_TEST_CFLAGS="-fsanitize=undefined -fno-sanitize-recover=all -g" .venv/bin/python -m pytest -q tests/test_factory_intent.py --basetemp=<another-new-path>
.venv/bin/python -m pytest -q --cov=native_e_lab --cov-branch --cov-fail-under=90 --basetemp=<third-new-path>
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
MYPYPATH=src:. .venv/bin/python -m mypy --explicit-package-bases -p native_e_lab -p research.real_cgroup -m research.admin_review.check_bundle
```

raw private fixture/intent/수명 로그는 Git에 넣지 않았다. 기존 잔여물이나 UNKNOWN D를 찾아 정리하지 않았다.
연구 branch의 local append-only commit과 bundle만 만들며 remote에는 게시하지 않는다.
새 Windows 진단 폴더에 최종 보고서·source·제한된 private 로그와 hash manifest를 전달한다.
제품 통합=NO, HOST/runtime qualification=NO.

다음 작업 하나: **기존 :1.0/job1 가정을 제거하는 동적 manager owner/job 결속 native backend를,
실제 관리자 연결 없이 private sd-bus fixture로 구현·검증**한다.
이는 protected system bus 연결·관리자 적용 승인이나 UNBOUND 해제가 아니다.
