# LOCAL NATIVE E — M-owned E / P / W 통합 보고서

STATUS: PASS_PRIVATE_COHORT_INTEGRATION_WITH_LIMITATIONS
날짜:2026-11-05
기준 revision:4643a9e7be574c6d3f9db114ebff7ce518777b5d
작업 branch:research/native-e-cohort-integration
최종 commit/CLEAN/전달 hash는 별도 FINAL_DELIVERY.json에 기록한다.

## 완료된 구현

기존 native private manager, parent handoff, 고정 worker-entry를 한 실행 경로로 연결했다.
실제 libsystemd private D-Bus를 거쳐 M이 E를 생성하고,
F가 원본 regular-P 핸들을 E에 전달하며 E가 고정 W를 exec한다.
이는 **동일 UID의 무권한 연구 fixture**다. 실제 PID1/systemd unit 또는 제품 provider가 아니다.

| 파일/API | 기능 |
| --- | --- |
| research/cohort_integration/cohort.c — ci_run_fixed(void) | 고정 orchestration, 원본 M wait, P grant/removal, late event와 불확실성 처리 |
| research/cohort_integration/peer.c — ci_peer_fixed(void) | 고정 fd0 진입, 상속 FD 차단, 기존 entry_peer/run_worker 연결 |
| tests/native/cohort_manager.c | test-only 새 M 생성, 실제 private SDK 메시지, 원본 E pidfd와 wait |
| tests/native/cohort_driver.c | test-only 실패 주입·shared-memory 생성/wait 횟수 계측 |
| tests/test_cohort_integration.py | native compile과 정상·오류45case |
| COHORT_INTEGRATION_DESIGN.md | 소유권·순서·한계 |
| COHORT_INTEGRATION_REVIEW.md | 독립 리뷰와 RED→GREEN 수정 |

기존 IPC framing, typed request parser, 원본 OFD 비교, sealed worker image,
NPG1/NWE1 protocol와 credential no-forward shim을 재사용했다.
원래92개 source/test/report 파일은 바이트 그대로 보존했고 PLAN/PROGRESS는 append-only다.
새 coordinator는 sequencing을 명시적으로 작성하며 이전 static helper를 include한다.
기존 구현을 새 manager/crossUID 자격이 있는 것처럼 바꾸거나 과거 evidence를 수정하지 않았다.
제품·패키지·실제 provider API에 통합하지 않았다.

## 실제 kernel/library 관측과 합성 경계

| 범위 | 이번 관측 |
| --- | --- |
| F→M, M→E, E→W 생성과 wait | native clone3 원본 pidfd. 정상 생성 각각1, wait 각각1 |
| F의 E/W handle 채택 | 없음. F는 M만, M은 E만, E는 W만 기다림 |
| private D-Bus endpoint | 실제 libsystemd의 h/SCM_RIGHTS, borrowed/owned lifetime 재사용 |
| regular P handoff | 새 일반 디렉터리 FD·OFD anchor·dev/ino·같은 context, E가 W 실행 동안 보유 |
| W 실행·진입 | 실제 sealed memfd execveat, fd0..3 진입 mask, kernel sender 및 parent/exec identity |
| UID/GID/cap/seccomp/NNP/PDEATHSIG 변경 | **no-forward shim으로만 합성**. 실제 보안 설정 변경 없음 |
| request의 User/caps/limits/ExecStart | **wire data**만 확인. M이 실제 계정·상한·systemd 실행을 적용하지 않음 |
| 실제 system/user bus·unit·cgroup D | NOT_RUN / UNIMPLEMENTED in this integration |
| protected origin/loader, F1, readonly mount, namespace containment | UNAVAILABLE / 미구현 |
| 외부 writer·async drain·임의 후손 소멸 | 미검증 |
| qualification16 / provider | available0, 모두UNAVAILABLE / UNBOUND |

P는 accepted manager job 이후 생성하므로 M/E에 상속되지 않는다.
M은 메시지를 받기 전에 상속된 F 핸들을 닫고,
E도 NPG1을 읽기 전에 상속된 bus/native FD를 닫는다.
W에는 host directory FD나 일반 자격증명·시크릿 환경을 전달하지 않는다.
고정 worker는 자기 exec/FD/parent metadata와 private protocol만 확인한다.

정상 순서:
private bus/job 확인 → 새 P → NPG1 GRANT/ACK/COMMIT/EOF →
E의 기존 W entry 검증 → P close → CLOSED/shutdown →
M의 원본 E wait → Unref/원본 M wait/final queue drain → F의 원본 P 제거.

M이 E endpoint duplicate를 보유하므로 E의 단순 close/exit로는 EOF가 되지 않는다.
명시적 shutdown 없이 성공으로 처리하지 않는다.
worker 생성 후 발생한 final ACK/late event 실패는 이미 관측한 worker birth를 지우지 않는다.
오류·취소 후 두 번째 Start/생성/wait는 하지 않는다.
모든 관측은 receipt/숫자 FD/PID로 권한을 복구하는 API와 분리돼 있다.

## 정리·실패 결과

정상 결과도 cleanup=CONFIRMED로 쓰지 않는다.
native handles의 관측 범위는 NATIVE_HANDLES_CONFIRMED_LIBRARY_UNAVAILABLE이며,
SDK 내부 close syscall 결과는 API가 노출하지 않아 library_close_result=UNAVAILABLE다.
native close/wait/name/OFD/부분 정리 결과가 불명확하면 UNKNOWN이다.
오류 뒤 P 디렉터리는 보존하며 자동 재부착·재삭제·반복 정리를 하지 않는다.

E worker reply 대기7500ms, M의 E 대기10000ms, F의 M 대기15000ms를 구분했다.
상한 이후 원본 pidfd 종료가 필요해도 임의 후손이 모두 drain됐다고 주장하지 않는다.
실패 fixture의 regular-directory residue와 관련 로그는 새 private test 경로에 보존돼 있다.
전체 HOST cleanup·악의적 동일 UID peer·원본 custody 또는 admission fence 성공은 미주장이다.
mkdir/open 및 이름검사/unlink의 틈은 trusted-single-owner 가정으로 남는다.
이전 internal-D UNKNOWN 실험은 조회·재접속·정리·성공 승격하지 않았다.

## 검증 결과

| 검사 | 실제 결과 |
| --- | --- |
| 신규 통합 tests | **45 PASS /0FAIL/0SKIP** |
| 전체 연구 회귀 | **493 PASS /0FAIL/0SKIP** = 이전448 + 신규45 |
| UBSan | 동일45case PASS. SDK shared library와 freestanding W는 계측 제외 |
| GCOV 실행 | 동일45case PASS. test-only child exit dump shim 사용 |
| 새 coordinator fixture C coverage | line93.43%(128/137), branch outcomes59.70%(160/268) |
| default-unbound compile variant | line24.82%(34/137), branch8.21%(22/268); fixture와 별도 |
| 새 E entry TU | line100%(5/5), branch outcomes50%(5/10) |
| synthetic M test code | line97%(97/100), branch outcomes61.98%(119/192) |
| 기존 Python coverage | 91.74%, 기준90 유지. 신규 C/SDK/kernel coverage와 별도 |
| GCC native compile | -std=c11 -O2 -Wall -Wextra -Werror PASS |
| Ruff / format | exit0 / exit0,60Python files |
| mypy | 기존 Python10modules exit0. C에 type 검사 통과를 붙이지 않음 |
| git diff --check / 보존 검사 | exit0 /92hashes 일치·ledgers append-only |
| 신규 package build | NOT_RUN, packaging 변경 없음 |
| 이전 제품2786PASS | 이번 NOT_RERUN, unchanged. fresh493에 합산하지 않음 |

반복·UBSan·GCOV·개발 RED를 unique PASS 수에 더하지 않았다.
native branch outcomes 전체 covered는 아니며 instrumentation은 SDK/kernel/systemd 자격을 측정하지 않는다.
coverage 분석은 fixture/default 두 compile variant를 분리했다.
초기 분석에서 같은 source key를 덮어쓰던 로그 집계 코드는 수정했고 위 수치는 분리된 최종값이다.

초기 신규 모듈 부재 RED 뒤 macro main 중첩과 test-only 경로 버퍼의 strict compiler 경고를 수정했다.
shared-memory audit 부재 RED를 추가한 후 원본 생성/wait 횟수 검증을 구현했다.
독립 source review의 Important P2:
첫 now_ms 실패값을 generation에 기록하고 두 번째 호출만 검사하던 문제가 있었다.
정확히 첫 context clock 조회만 실패시키자 전체 protocol/W 실행 성공으로 RED가 재현됐다.
한 번 읽은 값을 검사한 뒤 encode하도록 수정했다.
수정 후 정상/clock-failure2PASS, 전체493, UBSan45, GCOV45를 다시 확인했다.

Minor는 초기 PLAN의 P-before-M 문장과 실제 생성 순서 차이였다.
뒤의 append-only ruling과 설계에서 accepted job 뒤 P 생성 순서를 명시했다.
리뷰어는 다른 Important/Critical을 보고하지 않았다.
수정 이후 독립 재리뷰는 하지 않았으므로 final-tree 독립 C0/I0를 선언하지 않는다.

## 실제 환경·명령

이번 재확인:Ubuntu-24.04 WSL2, Linux6.18.33.2-microsoft-standard-WSL2/x86_64,
EUID1000/GID1000, CapEff0, 직접 exec NoNewPrivs0.
과거 호출과 같은 namespace/세대라고 가정하지 않고 매 fixture가 새 socket/process를 만든다.
기존 GCC·libsystemd.so.0·venv만 사용했다. 시스템 또는 개발 의존성을 새로 설치하지 않았다.
actual manager/systemd 설정 조회 확대·서비스 시작·관리자 승격·root 사용·cgroup 쓰기는 없었다.

~~~text
.venv/bin/python -m pytest -q tests/test_cohort_integration.py --basetemp=<new-private-path>
.venv/bin/python -m pytest -q --cov=native_e_lab --cov-branch --cov-fail-under=90 --basetemp=<another-new-path>
.venv/bin/python <private-delivery>/ubsan_runner.py
.venv/bin/python <private-delivery>/gcov_runner.py
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src/native_e_lab research/admin_review/check_bundle.py
git diff --check
~~~

테스트 basetemp는 매번 새 전용 경로만 사용한다. 이전 evidence 경로를 재사용하지 않는다.
instrument runner의 절대 경로는 새 복사본에서 새 로그 경로로 바꿔야 한다.
실제 실행 명령·exit code·제한된 로그는 전달 logs의 JSON/log에 있다.
제품 checkout은4b77b31dd23010f2d2b394466d88b04a4a2720e2/CLEAN,
기존 harness는9545d5422096fced078be1243cee98310499d25f/CLEAN으로 보존했다.
현재 remote main이라고 주장하지 않으며 fetch/pull/push/PR/merge 작업은 하지 않았다.

## 완료·미완료와 다음 작업 하나

완료: 새 manager-owned E→P→고정 W 연구 연결부, 오류/수명 테스트, 리뷰 수정, 재현 가능한 전달.
미완료: 실제 cgroup 내부 D 결합, 보호된 관리자 factory/코드/loader, crossUID 및 실제 HOST 자격.
실제 unit/계정/권한 적용은 이번 구현에 포함하지 않았다.

9개 qualification/admission flag와 나머지 actual_payload_released,cleanup_allowed,
recovery_execution_authorized,H_executed,HREQ004_qualified 등14개 전부false.
provider_registration=UNBOUND, qualification required16/available0/UNAVAILABLE.
고정 합성 worker 실행은 실제 H/차량 payload release와 다르다.

**다음 작업 하나: 이 manager-owned E 경로에 기존 E-owned internal-D supervisor를
연결하는 고정 합성 backend를 구현한다.**
현재 통합은 P와 W까지 확인하며 실제 D의 생성·정지·회수 경로는 아직 결합하지 않았기 때문이다.
이 후속 작업도 실제 관리자 권한이나 provider 자격을 자동 생성하는 단계가 아니다.
