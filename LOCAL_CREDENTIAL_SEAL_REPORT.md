# LOCAL CREDENTIAL SEAL REPORT

STATUS: PASS_UNPRIVILEGED_COMPONENT_FIXTURES
Provider / qualification: UNBOUND / 16 UNAVAILABLE
OS provisioning / fenced lab readiness: NO

## 실제 구현

[seal.c](research/credential_seal/seal.c)와 [seal.h](research/credential_seal/seal.h)에
고정 native credential-seal component를 구현했다. main/CLI/provider 등록/기존 lab 연결은 없다.
기존 제품·연구 runtime source/tests/config/옛 증거45개 파일은 SHA256 그대로 보존했다.
입력은 E/W 정책용 숫자 data이고 경로/PID/FD/명령/unit을 실행하는 public API가 아니다.
성공값 CE_SEALED_CREDENTIALS_ONLY는 RUN 허가·F1·원본 custody 또는 직렬화 가능한 권한이 아니다.
ce_attempt의 atomic 소비는 해당 메모리 instance에만 적용되며 복제 불가능한 capability라고 주장하지 않는다.

| API | 역할 |
| --- | --- |
| ce_build_id_filter(ids, out, capacity) | 실제 classic-BPF ID 인자 제한 program 생성. native x86_64 LP64만 지원 |
| ce_seal_worker(attempt, ids) | preflight → filter → group 제거 → GID/UID 전환 → ambient/cap 제거 → PDEATHSIG 재설정/조회 → readback |
| ce_seal_owner(attempt, ids) | E identity 유지, filter/group/cap 제거와 readback |

saved/filesystem 포함 네 UID/GID, supplementary groups, 다섯 capability field,
NNP, 단일 thread, 누락·중복·초과·손상 status를 확인한다. 실패하면 후속 mutation을 하지 않으며,
이미 시도한 작업은 UNKNOWN으로 남긴다. 원상복구나 alias/PID/path 재시도는 없다.
BPF는 credential-ID 변경만 제한하며 unrelated syscall을 허용한다. complete sandbox가 아니다.

## 실행하지 않은 것

실제 setresuid/setresgid/setgroups/capset/seccomp/prctl 보안 변경은 **0회**다.
테스트는 component의 syscall 심볼 전체를 test-only linker wrapper로 대체한다.
예상하지 못한 호출은 fixture를 종료하며 실제 syscall로 forwarding하는 경로가 없다.
BPF 판정은 독립 interpreter로 확인했다. kernel verifier/실제 filter 집행 성공으로 세지 않는다.
새 privileged worker/system unit/account/cgroup/manager 작업은 없다.
기존 회귀의 무권한 고정 direct-child 및 새 native test fixture process는 실행했다.
설치/업데이트/sudo/권한 승격/서비스 조작/Docker/차량/원격 push·PR·upload도 하지 않았다.

원본 parent 생존/custody, W exec-entry/FD 증명, 보호된 proc/manifest provenance,
F→E private IPC/P grant와 process-wide F1은 미구현/미검증이다.
seal을 실제 D 생성 전에 어떤 원본 factory phase에 연결할지도 다음 통합에서 검증해야 한다.
지금 component를 기존 바이너리에 연결해 높은 권한으로 실행해서는 안 된다.
Python sdist/wheel은 기존 package의 호환 build만 확인했다. 새 C component는 그 wheel에 포함하지 않는다.
신규 source/tests는 연구 branch·전달 폴더·Git bundle로 인계한다.

## 검증 결과

| 검증 | 최종 결과 |
| --- | --- |
| 연구 pytest | **236 PASS / 0 FAIL / 0 SKIP** = 기존178 + 신규58 |
| 기존 제품 pytest | **2786 PASS / 0 FAIL / 0 SKIP** |
| 중복 없는 최종 합계 | **3022 PASS**. focused/이전 단계 수치는 중복 합산하지 않음 |
| 연구 Python coverage | 91.74%, 기존90 기준 유지. 신규 C coverage와 별개 |
| 제품 coverage | 98.50%, 기존90 기준 유지 |
| 신규 C fixture gcov | line100.00%(128), executed-branches98.90%, outcomes-taken82.42%(182) |
| UBSan | interposed fixture37회 exit0, kernel/privilege 실험 아님 |
| C compile | C11/Wall/Wextra/Werror, fixture와 component build 성공 |
| ruff / format / mypy | exit0. type 대상은 기존 Python9modules, C의 type 검증이 아님 |
| 기존 package sdist/wheel | 새 output directory에서 build exit0, 전역 install 없음 |

기록한 실패도 보존한다. 최초 미구현 RED, transaction RED30/20, 초기 style 실패를 수정했다.
독립 리뷰는 x32 guard 결함과 readback 오류 주입 부족을 지적했다.
실제 compile guard와 fault case RED7/positive1을 재현한 뒤 한 번의 수정 pass로 해결했다.
중첩 reentry case도 추가했다. [리뷰 기록](CREDENTIAL_SEAL_REVIEW.md)에 원래 SHA와 범위를 기록했다.
수정 뒤 전체 독립 재리뷰는 하지 않아 C0/I0를 선언하지 않는다. 작성자의 TDD·전체 회귀 검증 결과다.

제품 회귀 첫 시도는 NumPy 없는 연구 venv에서 **2675 PASS/111 FAIL**이었다.
실패 case 이름/trace는 product-regression.txt에 보존했다. 기존 NumPy 환경인 harness/.venv로
같은 제품 checkout을 재검증해2786 PASS를 확인했다. 설치나 기준 완화는 하지 않았다.
소스 조회에서 rg 부재는 제한된 Python 읽기로 대체했고, 진단 로그 경로의 slash 구성 오류1회도 수정했다.
이 진단 오류를 product/runtime 오류 또는 성공으로 섞지 않는다.

## 소스와 재실행

Base: f5c62ac0186e486f88d2cbb3e764e8da036e954a
Branch: research/native-e-credential-seal, 기존 isolated linked worktree에서 분기.
기존 research/native-e-provisioning-plan, admission-design, internal-d, native-e-local과 제품 main은 보존한다.
최종 commit/상태/파일 hash/bundle은 전달 폴더 FINAL_DELIVERY.json에 있다.

전용 연구 venv에서:

~~~text
.venv/bin/python -m pytest -q tests/test_credential_seal.py
.venv/bin/python -m pytest -q --cov=native_e_lab --cov-branch --cov-fail-under=90
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src/native_e_lab
~~~

tests가 cc로 test-only interposed fixture를 빌드한다. 실제 권한 전환용 executable 실행 명령은 제공하지 않는다.
제품 회귀는 이미 설치된 NumPy 포함 harness venv와 제품 src PYTHONPATH를 사용했다.
정확한 명령·exit 및 앞선 실패는 logs에 보존한다. 기존 테스트 삭제·threshold 변경은 없다.

## 로컬 작업은 언제까지인가

노트북을 native E 실행 호스트로 검증하는 목표이므로, 나중의 한정된 관리자 OS lab도 이 호스트에서 한다.
무권한 구현 단계의 남은 코드 준비는 두 묶음이다.

1. 원본 F→E private 연결과 새 P grant의 생성 시점 handoff/FD 수명.
2. 다른UID W의 원본 exec-entry/FD 및 parent 관계 증명, 두 component의 고정 통합.

두 묶음의 회귀·review가 통과하면 정확한 artifact/IPC/unit 변경안을 채워 관리자 변경 검토로 넘어갈 수 있다.
이번58개 test만으로 그 시점을 앞당기거나 실제 권한 변경을 자동 승인하지 않는다.
새 결함이나 OS 제약이 발견되면 그 blocker를 명확히 보고한다. 완료 날짜나 통과를 미리 약속하지 않는다.
그 한정 OS lab 성공도 full native E/provider 자격이나 실제 H/차량 readiness와 별개다.

**다음 작업 하나: 격리된 무권한 fixture에서 원본 F→E private 연결과 원본 P grant handoff를 구현한다.**
실제 system unit/cgroup 변경 없이 연결 생성·FD 수명·EOF/중복/replay 거부를 먼저 검증할 수 있다.

모든14 승인 flag는 false, actual payload 미실행, UNBOUND/16UNAVAILABLE 유지.
[C source의 API 근거](https://man7.org/linux/man-pages/man2/seccomp.2.html),
[capset 구조](https://man7.org/linux/man-pages/man2/capset.2.html),
[kernel seccomp의 범위](https://docs.kernel.org/userspace-api/seccomp_filter.html)는 구현 참고이며 현재 호스트의 집행 증거가 아니다.
