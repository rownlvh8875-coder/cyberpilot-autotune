# LOCAL NATIVE E — 내부 D / manager-owned cohort 통합

STATUS: PASS_SYNTHETIC_DOMAIN_COHORT_WITH_LIMITATIONS
날짜:2026-11-05
기준 revision:d70b425bb061c710fd0aabe2fdd396c765d16770
branch:research/native-e-domain-cohort
최종 commit/CLEAN/전달 해시는 별도 FINAL_DELIVERY.json에 기록한다.

## 구현 결과

**E가 전달받은 원본 P에서 D를 생성하고, 고정 W의 진입 검증·단일 stop·원본 wait·회수를 수행하는 연구 연결부를 구현했다.**
이번 cgroup 경계는 **일반 private 디렉터리 위의 가상 계층**이다.
실제 clone/exec/OFD/pidfd/SIGKILL/wait와 실제 cgroup containment를 구분한다.

| 파일/API | 역할 |
| --- | --- |
| research/domain_cohort/policy.c / internal.h | hidden 내부 D 상태·원본 핸들·단일 stop/write/wait·회수 |
| research/domain_cohort/peer.c | 고정 E의 NPG1 live P와 D/W 경로 연결 |
| research/domain_cohort/worker.c | 기존 static entry witness 재사용, 최대4500ms 대기 후 정상 exit42 |
| tests/native/domain_cohort_driver.c | 가상 cgroup metadata·placement·kill, 실제 원본 pidfd와 native 오류 주입 |
| tests/test_domain_cohort.py | 고정 source-pin 조합·strict build·31개 native fixture |
| DOMAIN_COHORT_DESIGN.md | 소유권·순서·불확실성 |
| DOMAIN_COHORT_REVIEW.md | 독립 리뷰 Important2와 RED→GREEN |

기존101개 source/test/report는 바이트 그대로 보존했다. PLAN/PROGRESS는 append-only다.
기존 domain supervisor의 original_D, exactly_child, no_descendants, wait_domain_original을 재사용한다.
경로로 P를 다시 찾는 옛 launcher는 호출하지 않는다.
정확히 hash가 고정된 옛 source의 main을 build 시 rename해 helpers를 조합했다.
test driver도 같은 방식으로 고정 source와 wrapper만 연결했다.
생성된 reference C는 임시 build 입력이며 OS 원본 진위나 protected-origin 증거가 아니다.
기존 credential/image/trampoline/IPC/manager 코드는 수정하지 않았다.

top-level 고정 실행 외에 호출자가 임의 경로·명령·unit·PID·FD번호·receipt를 넘기는 API는 없다.
hidden 내부 interface의 P는 고정 E가 NPG1로 받은 live reference다.
새 provider/public library API나 실행 자격 레코드를 만들지 않았다.

## 실제 관측과 가상 계층

| 범위 | 결과 |
| --- | --- |
| F→M→E→W 생성·원본 pidfd | 실제 kernel, 각각의 부모가 원본 child만 관리 |
| sealed static W exec/FD/부모/SCM_CREDENTIALS | 기존 실제 kernel witness 재사용 |
| P/D 디렉터리·OFD·이름 교체·close | 새 일반 private 디렉터리에서 실제 동작 |
| CLONE_INTO_CGROUP 요청 | 새 E source가 원본 D FD를 넣어 요청 |
| 실제 cgroup 배치 | **미실행**. test shim이 그 bit만 제거하고 실제 child 생성 |
| D metadata·cgroup.kill | **가상 계층**. 새 일반 파일만 읽고 씀 |
| worker 종료·wait | kill simulator가 birth 때 유지한 원본 pidfd만 signal, 실제 SIGKILL/wait |
| 실제 kernel cgroup.kill | 미실행 |
| UID/GID/cap/seccomp 변경 | 신규 경로는 기존 no-forward shim으로만 합성 |
| systemd manager·unit·controller·namespace·Docker·차량 | 신규 접근/변경/실행 없음 |
| 실제 provider·qualification | UNBOUND /16UNAVAILABLE, available0 |

정상 계측은 D생성1 / born-in-D요청1 / kill쓰기1 / 원본 W wait1 / D회수1이다.
이 수치를 실제 kernel cgroup 생성·배치·kill 성공으로 읽으면 안 된다.
가상 kill은 숫자 PID로 대상에 다시 붙지 않고, E가 생성 당시 받은 원본 pidfd를 사용한다.
W의 정상 exit42나 exit137 값은 정확한 CLD_KILLED/SIGKILL로 인정하지 않는다.

순서:
원본 P grant → E의 새 D 생성·anchor → 원본 D에 W birth 요청 →
고정 W entry proof → 정확히 W만 멤버·후손0·원본 P/D 확인 →
단 한 번 stop open/write → 원본 pidfd 소비 후 정확한 SIGKILL wait →
유일한 populated0·원본 D 확인 → D회수/핸들close →
E 완료 → M/F 원본 wait·마지막 event 검증 → F의 P 회수.

E는 검사된 D 멤버가 아니어야 하고, 후손이나 추가 멤버가 보이면 stop을 거부한다.
실제 namespace containment 또는 coequal writer에 대한 admission fence는 구현하지 않았다.
mkdir/open 및 검사/stop/unlink 사이 틈도 trusted-single-owner 가정으로 남는다.

## 불확실성·잔여 자원

stop은 open/write 전에 소비한다. 부분·unknown write 뒤 두 번째 stop/signal을 보내지 않는다.
그 뒤에는 원본 W를 한 번 기다리고, 고정 W의 제한된 자연 종료도 성공으로 승격하지 않는다.
stop 전 실패는 E가 만든 원본 W만 한 번 정지·wait할 수 있다.
wait 시도는 원본 핸들을 먼저 소비하므로 unknown 이후 cleanup이 다시 wait하지 않는다.

부모 OFD anchor가 없으면 inode가 같아도 숫자 FD를 닫지 않는다.
process-bound UNKNOWN으로 남기며 해당 process의 종료에 따른 FD table 회수와 명시 close 성공을 구분한다.
D 이름/OFD 변경, unknown wait/close, 회수 실패에서는 자동 재접속·삭제·재시도를 하지 않는다.
가상 디렉터리 잔여물과 실패 로그는 새 private 시험 경로에 보존했다.
D 제거가 실제 발생한 뒤 close/return 오류가 나면 audit의 D_removed=1은 유지하지만 전체 결과는 실패다.
그때도 F가 P를 자동 회수하지 않는다.

정상 결과조차 SDK 내부 close 결과는 UNAVAILABLE다.
NATIVE_HANDLES_CONFIRMED_LIBRARY_UNAVAILABLE를 전체 HOST cleanup 성공으로 표현하지 않는다.
임의 후손·외부 writer·async drain·악의적 E에 대한 attestation은 미검증이다.
과거 internal-D UNKNOWN 실험은 다시 조회·정리하거나 성공으로 바꾸지 않았다.

## 테스트·리뷰

| 검증 | 최종 실제 결과 |
| --- | --- |
| 신규 native 통합 | **31 PASS /0FAIL/0SKIP** |
| 전체 연구 회귀 | **524 PASS /0FAIL/0SKIP** = 이전493 + 신규31 |
| UBSan | 동일31 PASS. SDK·static W·kernel은 계측 제외 |
| GCOV 실행 | 동일31 PASS, child dump는 test-only exit shim |
| 새 policy.c | lines100%(63/63), branch outcomes70.29%(97/138) |
| 새 peer.c | lines97.89%(93/95), branch outcomes61.18%(104/170) |
| test driver | lines97.01%(130/134), branch outcomes78.14%(193/247), 제품 코드와 별도 |
| 기존 Python coverage | 91.74%, 기준90 그대로 |
| C build | -std=c11 -O2 -Wall -Wextra -Werror PASS |
| Ruff / format | exit0 / exit0,64Python files |
| mypy | 기존 Python10modules exit0. C type 인증으로 표현하지 않음 |
| 보존 검사 | 기존101hashes 일치, ledgers append-only |
| Python wheel/package build | NOT_RUN, packaging 변경 없음 |
| 이전 제품2786PASS | 이번 NOT_RERUN, unchanged. fresh524에 합산하지 않음 |

UBSan·GCOV·반복 실행·개발 RED는 unique PASS에 더하지 않았다.
native branch outcomes 전체를 실행한 것은 아니며 SDK/systemd/kernel coverage로 승격하지 않는다.

독립 source review는 Important2, Critical0/Minor0이었다.
첫 W generation clock 조회만 실패시키자 전체 성공/D회수가 일어나는 RED를 재현했다.
단일 int64 조회값을 검사한 뒤 encode하도록 수정했다.
partial parent FD를 같은 inode·다른 OFD로 교체한 RED에서는 foreign close1이 관측됐다.
anchor 미확립 시에는 close하지 않는 UNKNOWN 정책으로 수정해 foreign close0을 확인했다.
수정 뒤 정상+두 실패 case3PASS, 전체524/UBSan31/GCOV31을 재검증했다.
수정 이후 독립 재리뷰/C0/I0는 선언하지 않는다. 보고서/evidence는 author 검증이다.

초기 fixture의 이름 교체용 mkdir까지 component의 D생성으로 집계하던 오류도 수정했다.
source 기준이나 테스트 합격 기준을 낮추지 않았다.
기존 테스트는 삭제하거나 수정하지 않았다.

## 환경·재실행

이번 재확인:
Ubuntu-24.04 WSL2, Linux6.18.33.2-microsoft-standard-WSL2/x86_64,
직접 실행 EUID1000/GID1000, CapEff0, NoNewPrivs0.
새 호출의 namespace/세대가 과거와 동일하다고 가정하지 않았다.
기존 GCC/libsystemd/venv만 사용했다. 새 의존성·시스템 패키지 설치 없음.

~~~text
.venv/bin/python -m pytest -q tests/test_domain_cohort.py --basetemp=<fresh-private-path>
.venv/bin/python -m pytest -q --cov=native_e_lab --cov-branch --cov-fail-under=90 --basetemp=<another-fresh-path>
.venv/bin/python <private-delivery>/ubsan_runner.py
.venv/bin/python <private-delivery>/gcov_runner.py
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src/native_e_lab research/admin_review/check_bundle.py
git diff --check
~~~

실제 command/exit code는 전달 logs의 JSON/log에 기록했다.
instrument runner는 새 복사본에서 private log 경로를 조정해야 한다.
basetemp는 새 경로만 사용하고 기존 evidence 경로를 재사용하지 않는다.
새 backend의 보안 syscall은 no-forward다.
전체 회귀에는 기존 직접 자식의 NNP/rlimit self-restriction 검사도 그대로 포함된다.
이를 신규 credential proof나 시스템 전역 설정 변경으로 표현하지 않는다.

제품 checkout4b77b31dd23010f2d2b394466d88b04a4a2720e2와
기존 harness9545d5422096fced078be1243cee98310499d25f는 CLEAN으로 보존했다.
현재 remote main이라고 가정하지 않았고 fetch/pull/push/PR/merge를 하지 않았다.
관리자 승격·기존 서비스 start/restart/stop·전역 설정·실제 cgroup 쓰기·차량 작업은 없었다.

## 완료 범위와 다음 작업 하나

완료: manager-owned E의 live P → 새 D → 고정 W → 단일 stop/wait/회수의 native 연구 연결부와 회귀.
미검증: 실제 cgroup 배치/kill, 실제 관리자 factory, protected origin/loader,
cross-UID, F1, readonly mount, namespace containment, HOST/runtime 자격.
원래16종 qualification 증거는 모두 UNAVAILABLE이며 이 fixture로 채우지 않았다.
기존14개 승인 flag는 전부false, provider_registration=UNBOUND 유지.
고정 합성 worker 실행은 actual H/product/vehicle payload release와 별도다.

**다음 작업 하나: 기존 승인 범위의 새 user-unit lab에 실제 cgroup2를 연결하는 고정 adapter를 구현·검증한다.**
현재 연결부는 가상 controller 경계까지만 검증했으므로 실제 kernel 배치·kill은 별도 실험이 필요하다.
이 다음 작업도 실제 provider 등록·실차 적용·관리자 권한의 자동 승인을 뜻하지 않는다.
