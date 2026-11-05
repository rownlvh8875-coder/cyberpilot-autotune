# LOCAL PRIVATE PARENT HANDOFF REPORT

STATUS: PASS_NATIVE_PRIVATE_PARENT_HANDOFF_FIXTURE
Actual provider: UNBOUND / qualification16: UNAVAILABLE
OS provisioning readiness: NO

## 완료한 구현

[고정 native F/E](research/parent_handoff/handoff.c)가 실제 socketpair와 SCM_RIGHTS를 사용해
새 private 일반 디렉터리 P의 FD를 전달한다. 실제 systemd/cgroup parent grant는 아니다.
F가 P와 연결을 생성하고 원래 E pidfd를 clone3 birth에서 보유한다. Python controller의 spawn 반환에
E의 원본 소유권을 맡기지 않는다. E는 수신 전에 inherited FD3이상을 닫고 control endpoint를0으로 한정한다. 표준 진단 stdout/stderr1/2는 남는다.
그다음 parent FD를 받아 local OFD anchor를 유지하고, 종료 뒤 F가 원래 pidfd로 한 번 wait한다.
외부 PID/path/FD/명령/unit을 채택하는 CLI나 receipt 기반 recover API는 없다.

NPG1 protocol은 HELLO→READY→GRANT→ACK→COMMIT→EOF→CLOSED다.
50-byte cohort/generation/nonce/sequence 필드와 최대512-byte framing을 사용한다.
단계 전체에2.5초 절대 deadline을 적용한다. GRANT에만 정확히1개의 CLOEXEC directory FD를 허용한다.
prefix/body 어느 chunk에서 온 ancillary라도 수집하고, 중복/초과/절단/다른 단계 FD를 거부·종료한다.
short/error send는 이미 권리를 전달했을 수 있어 재전송하지 않는다.
기존 worker protocol은 수정하지 않았으며 여전히 모든 ancillary를 거부한다.

COMMIT 뒤 EOF를 확인하기 전에는 parent를 승인하지 않는다. W/payload/RUN 단계는 없다.
CLOSED는 실제 수신 ref 종료 뒤 보내며, F는 E의 종료와 channel EOF도 확인한다.
FD 숫자가 다른 대상으로 재사용되면 감지한 foreign FD를 닫거나 이름으로 다시 붙지 않는다.
이 검사는 적대적 동시 FD-table 변경을 막는 OS fence가 아니다.

## 실제 수행 범위와 한계

실제 수행: 새 ordinary native F/E process, private 일반-directory 생성, kernel FD transfer,
local kcmp/OFD 검사, 수신 ref 종료, original pidfd wait, 조건부 신규 directory 제거.
권한/계정/credential/security 설정 변경, 실제 cgroup 생성·write, systemd unit/service 작업,
Docker, 장치/Jetson/차량 접근, payload 실행은 하지 않았다.
모듈은 root 실행과 cgroup v1/v2 filesystem에서의 생성도 거부한다.
이 거부 test는 fstatfs 경계 주입이며 실제 cgroup 생성 실험이 아니다.

같은 UID의 trusted single-owner fixture다. 새 일반 P의 source가 고정돼 있다는 조건과
kernel SCM_RIGHTS/OFD 동작을 검증했으며, 동권한 공격자 배제나 보호된 code origin을 증명하지 않았다.
E의 fstat/dup/kcmp가 혼자서 F의 host 권한이나 최초 mkdir inode의 atomic custody를 증명하지 않는다.
실제 systemd P 생성과 original private IPC binding은 별도 미검증이다. worker exec-entry/FD/parent proof도 없다.
현재 결과를 native E 전체/16종 증거/실차 readiness로 승격하지 않는다.

## 정리와 잔류

불확실성이 제거 전에 발생하면 P를 남기고 경로/PID/receipt로 복구하거나 재시도하지 않는다.
P 제거가 먼저 성공한 뒤 마지막 base FD close가 UNKNOWN이 될 수 있다.
이때 parent_removed=true와 cleanup=UNKNOWN을 함께 보존한다. 디렉터리를 다시 만들지 않는다.
UNKNOWN을 성공으로 바꾸거나 원본 handle 대신 숫자/이름으로 같은 작업을 다시 보내지 않는다.
negative test의 새 private P, 진단 출력과 계측 실패 residue는 보존했다. 기존 사용자 자원은 정리하지 않았다.

## 검증

| 항목 | 최종 결과 |
| --- | --- |
| 신규 handoff tests | **33 PASS / 0 FAIL / 0 SKIP** |
| 전체 연구 tests | **269 PASS** = 기존236 + 신규33 |
| 기존 제품 tests | **2786 PASS** |
| 중복 없는 최종 합계 | **3055 PASS / 0 FAIL / 0 SKIP** |
| 기존 연구 Python coverage | 91.74%, 기준90 유지. 신규 C와 별도 |
| 제품 coverage | 98.50%, 기준90 유지 |
| 신규 handoff.c 계측 | lines96.57%(204), branches-executed98.01%, outcomes-taken72.52%(302) |
| UBSan | 고정 native fixture33case 통과 |
| fault wrapper 없는 native binary | strict O2 build와 정상 handoff/회수 PASS |
| Ruff/format/mypy | exit0. mypy 대상은 기존 Python9modules |
| 기존 Python sdist/wheel | 새 output에 build exit0. 신규 C는 wheel 통합 안 함 |

GCOV child의 _exit 전 dump와 libgcov file lock용 forwarding은 copied test driver의 계측 전용 수정이다.
production source를 바꿔 coverage를 높이지 않았다. kernel/systemd coverage 수치가 아니다.
첫 계측 시도는 wrapper가 libgcov의 fcntl lock을 거부해 exit97이었다.
그 cohort의 실패와 residue는 유지하고, 계측 shim 수정 후 새 private cohort에서 측정했다.
ordinary tests/UBSan/fault 없는 실행은 그 계측 shim과 분리한다.

개발 중 실패도 기록했다. 최초 missing-component RED, close fault 미발동 test 오류,
생성 전 filesystem gate와 F_GETFD 음수 처리의 RED→GREEN을 보존했다.
독립 리뷰는 cgroup-v1 gate/후제거 close contract/FD 카운터를 지적했다.
한 번의 수정 pass에서 source guard, targeted test와 OFD-generation별 close-attempt tracker를 보완했다.
중간 test-only forward declaration 오류의33 compile 실패도 보존했다.
[리뷰 기록](PARENT_HANDOFF_REVIEW.md)에 원래 SHA/지적/제외 범위가 있다.
수정 뒤 독립 재리뷰는 하지 않아 C0/I0를 선언하지 않는다. 작성자의 TDD·전체회귀 결과다.

## 소스와 실행 명령

Base: a961f2ce2d3a50b5989ec75902352f5954f94ad4
Branch: research/native-e-parent-handoff
기존 isolated worktree를 재사용했다. 제품 checkout은 main 4b77b31dd23010f2d2b394466d88b04a4a2720e2로 고정해 검사했다. 기존 tracked source/tests/config/보고·증거52파일은 SHA 그대로다.
PLAN/PROGRESS는 append-only다. 이전 branch와 제품 main은 이동시키지 않았다.
로컬 commit/bundle/최종 hash/CLEAN은 FINAL_DELIVERY.json에 기록한다. push/merge/PR/upload는 하지 않는다.

~~~text
wsl.exe --distribution Ubuntu-24.04 --exec /usr/bin/python3 -I -B -
.venv/bin/python -m pytest -q tests/test_parent_handoff.py
.venv/bin/python -m pytest -q --cov=native_e_lab --cov-branch --cov-fail-under=90
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src/native_e_lab
~~~

제품 회귀는 기존 NumPy 포함 harness venv와 제품 src PYTHONPATH를 사용했다. 새 의존 설치는 없다.
명령/exit와 source별 계측은 private 전달 logs에 보존한다. 테스트 기준/기존 테스트를 변경하지 않았다.

## 다음 작업 하나

**고정 W exec-entry/FD/parent 관계 증명과 credential·handoff component 통합을 무권한 fixture로 구현한다.**
이후에도 protected systemd factory와 실제 host 권한 검증은 별도 gate다.
지금까지의 무권한 component 결과로 관리자 변경을 자동 승인하지 않는다.
provider_registration=UNBOUND,16종 available0/UNAVAILABLE, 모든14 승인 flag=false를 유지한다.

[SCM_RIGHTS 동작](https://man7.org/linux/man-pages/man7/unix.7.html),
[recvmsg 제어 데이터](https://man7.org/linux/man-pages/man2/recvmsg.2.html),
[clone3 pidfd](https://man7.org/linux/man-pages/man2/clone.2.html),
[kcmp OFD](https://man7.org/linux/man-pages/man2/kcmp.2.html)는 구현 근거이며 자격 증거가 아니다.
