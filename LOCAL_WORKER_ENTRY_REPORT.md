# LOCAL FIXED WORKER ENTRY / INTEGRATION REPORT

STATUS: PASS_SAME_UID_FIXED_ENTRY_RESEARCH_FIXTURE
제품/provider 통합: 미완료. 실제 HOST/runtime 자격 부여: 없음.
Base: 42b7711ea6af2b9802eff60715e5fe002e525d5d
Branch: research/native-e-worker-entry

## 완료한 구현

[고정 F/E/W integration](research/worker_entry/integration.c)가 기존 private P handoff와
credential component, 고정 W의 exec-entry 검사를 연결한다.
[credential 연결부](research/worker_entry/entry_credential.c)는 기존 seal.c를 별도 translation unit으로,
integration은 기존 handoff.c helper를 include해 재사용한다. 기존58파일은 변경하지 않았다.
[fixed_worker.c](research/worker_entry/fixed_worker.c)는 libc·동적 loader 없는 static x86_64 ELF다.
외부 path/PID/FD/명령/unit/payload/receipt를 채택하는 실행·복구 API는 없다.
현재 Python package/provider/실제 HOST 또는 estimator/application에는 연결하지 않았다.

E는 prebirth filter phase→W birth→W seal/E owner seal 순서를 사용한다.
단, 이번 실행에서 credential TU의 syscall은 테스트 전용 no-forward shim으로 전부 교체했다.
고정 synthetic ID17001/17002→18001/18002, capability/filter/drop/PDEATHSIG 효과는 모의다.
실제 W의 UID/GID는 현재 사용자다. 실제 credential/security syscall 변경은0회다.
shim 없는 binary는 현재 사용자 환경의 preflight에서 W birth 전에 거부했다.
이를 다른 UID·capability·NNP 구성에서도 안전하게 배포할 수 있다는 증거로 사용하지 않는다.

## 원본 exec·FD·parent 관계

E가 fixed adjacent ELF를 검사하고 새 memfd에 복사한 뒤 WRITE/GROW/SHRINK/SEAL을 적용·readback한다.
원본 sealed FD와 OFD anchor를 보유한다. write/truncate 거부와 원래 source 이름의 bytes 교체 후에도
봉인한 원본 실행이 유지되는 것을 테스트했다. bounded/static/type/owner/mode 검사와 봉인은
보호된 code origin, 패키지 진위, readonly mount의 대체 증거가 아니다.

실제 clone3 원본 W pidfd, CLOEXEC exec-error pipe, kernel SCM_CREDENTIALS와
신뢰한 고정 W의 self exe device/inode·parent·FD witness를 함께 대조한다.
exec-pipe EOF 또는 PID 일치만으로 통과시키지 않는다.
preexec 가짜 witness, exec error, early exit, 다른 sender/image/parent/FD mask를 거부했다.
socketpair의 SO_PEERCRED는 생성 당시 creator를 가리키므로 W sender 검증에 사용하지 않는다.
[Linux UNIX socket 설명](https://man7.org/linux/man-pages/man7/unix.7.html)

E는 /proc/<W>/exe/fd를 조회하지 않아 ptrace 권한을 추가하지 않는다.
W의 exec entry에는 /dev/null0..2와 private socket3만 남는다.
exec FD4/error FD5는 CLOEXEC이다. 원래 E pidfd6은 seal 전후 생존과 getppid를 확인하고
exec 전에 닫는다. 그 외 inherited FD는 close_range로 닫는다.
worker가 여는 self-probe FD는 검사 뒤 닫는다.
[empty-path execveat](https://man7.org/linux/man-pages/man2/execveat.2.html)

이 관계는 감사한 고정 코드와 trusted same-UID fixture에 의존한다.
악의적인 E/trampoline 또는 동권한 공격자를 배제하는 독립 attestation은 아니다.
실제 cross-UID exec/seal 통합과 host protected-code origin은 미검증이다.

## Protocol과 수명

기존 NPG1 private parent handoff는 유지한다.
새 NWE1은50-byte cohort/generation/nonce/sequence 문맥과
BIND→ENTRY→FINISH→EOF→DONE→EOF 순서를 사용한다.
512byte 상한, 고정 worker의2.5초 protocol deadline을 적용한다.
nonempty receive chunk마다 원래 W의 kernel sender PID/UID/GID를 요구한다.
Linux stream EOF에서 관측한 단일 zero credential은 sender 증거로 쓰지 않는다.
zero-length frame, 추가 bytes/control, 다른 문맥·순서·FD·잘린 frame은 거부한다.
original monotonic clock을 사용할 수 없으면 새 entry preflight/reader는 거부한다.
이 deadline 관측은 H profile 또는 hard realtime 안전 자격이 아니다.

F는 E의 W timeout·original wait가 끝날 수 있게 별도 bounded 대기를 한다.
stop/wait는 보유한 원래 pidfd로만 수행하며 이름/PID/path/receipt로 복구하지 않는다.
불확실한 close/wait/send는 UNKNOWN이고 같은 작업을 재시도하지 않는다.
W birth는 단조롭게 보존한다. 이후 최종 parent ACK가 실패해도 true를 false로 바꾸지 않는다.
E의 최종 상태를 확인할 수 없으면 worker_started/peer_exit를 null로 남긴다.

## 실제 실행과 모의 검사의 구분

| 항목 | 이번 결과 |
| --- | --- |
| 고정 same-UID W, sealed memfd exec, 원래 pidfd | 실제 kernel fixture PASS |
| SCM_RIGHTS P 전달·SCM_CREDENTIALS W sender | 실제 local IPC PASS |
| self exe/FD/parent 대조, 봉인/이름 교체 검사 | 실제 fixed-code fixture PASS |
| credential UID/group/capability/seccomp/PDEATHSIG 변경 | 전부 test-only simulation. 실제 변경0 |
| shim 없는 현재 사용자 preflight 거부 | 실제 PASS, W 미생성 |
| protected systemd F/unit/private IPC binding | 미구현/미검증 |
| 실제 cross-UID credential/exec | 미실행 |
| 실제 cgroup D와 새 component 결합 | 미구현/미검증 |
| admission fence/namespace/readonly mount | 미구현/미검증 |
| 외부 writer/async drain, arbitrary descendant containment | 미검증 |
| OS/systemd unit/service/Docker/차량/원격 host 작업 | 미실행 |

negative test는 주로 fail-closed 출력과 특정 FD/wait 경계의 counter를 검증한다.
F→E 및 E→W 생성 반환의 취소 fixture를 다뤘지만, 모든 negative-path FD leak 부재나
임의 descendant drain을 증명하지 않는다. 과거 internal-D 결과는 해당 과거 revision에만 유효하다.
현재 component의 전체 자격으로 전이하지 않았다.

## 최종 검증

| 검사 | 결과 |
| --- | --- |
| 신규 worker entry tests | 60 PASS /0FAIL/0SKIP |
| 전체 연구 tests | 329 PASS = 기존269 + 신규60 |
| 기존 제품 regression | 2786 PASS /0FAIL/0SKIP |
| 중복 없는 합계 | **3115 PASS /0FAIL/0SKIP** |
| 연구 Python coverage | 91.74%, 기존 기준90 유지 |
| 제품 Python coverage | 98.50%, 기존 기준90 유지 |
| UBSan | 신규60case PASS, E/helper/credential/shim 경계 계측 |
| freestanding fixed_worker | strict static compile + 기능 검사. UBSan 계측 제외 |
| 신규 C line/branch coverage | UNAVAILABLE. Python coverage에 포함하지 않음 |
| GCC strict compile | -std=c11 -O2 -Wall -Wextra -Werror PASS |
| Ruff check/format | exit0 |
| mypy | 기존 Python9modules, exit0 |
| 기존 Python sdist/wheel build | --no-isolation exit0. 신규 연구 C는 wheel 미포함 |
| 원래 tracked58파일 보존 | SHA25658/58, PLAN/PROGRESS append-only |
| 제품/harness 기존 worktree | HEAD 유지, CLEAN |

환경: Ubuntu-24.04 WSL2, kernel6.18.33.2-microsoft-standard-WSL2, x86_64,
EUID1000, CapEff0, 직접 실행 NoNewPrivs0, GCC13.3.0.
매 fixture는 새 process/cohort를 사용한다. WSL 호출 간 동일한 namespace·세대를 가정하지 않는다.
제품 회귀 기준은 main4b77b31dd23010f2d2b394466d88b04a4a2720e2이며 최신 remote라고 주장하지 않는다.
기존 numpy 포함 venv를 재사용했고 의존성 설치는 하지 않았다.

개발 실패와 수정도 보존했다. missing-component RED, compiler 경고,
source mode mask, Linux EOF credential 재현, seal 후 parent 생존 확인 누락,
clock unavailable, 최종 ACK 뒤 birth 정보 소실을 각각 확인·수정했다.
UBSan 첫 실행53PASS/2FAIL은 fortified __poll_chk가 test fault wrapper를 우회한 문제였다.
동일한 경계에 wrapper를 추가한 후 최종60PASS다. 생산 기준을 완화하지 않았다.
중간 logging wrapper의 json import 오류는 테스트 완료 뒤 발생했으며 최종 command/exit를 다시 기록했다.
중간 및 최종 실행 횟수를 PASS 합계에 더하지 않았다.

[독립 리뷰 기록](WORKER_ENTRY_REVIEW.md)의 Important1건과 Minor1건을 재현 테스트로 수정했다.
리뷰어는 production 수정본을 소스로 다시 읽었고 실제 OS 실험은 수행하지 않았다.
최종 test-shim Minor 수정 뒤의 검증은 작성자 회귀다. 전체 final-tree C0/I0 인증은 선언하지 않는다.

## 자원·보존 상태

이번 새 regular private P, socketpair, sealed memfd, fixed child와 빌드 산출물만 사용했다.
성공 fixture는 원래 child wait/종료와 신규 P 제거를 확인했다.
UNKNOWN negative fixture의 P와 제한된 logs는 보존하고 재부착·수동 cleanup/recovery하지 않았다.
최종 basetemp는 전용 logs 아래 새 경로를 사용했다.
초기 pytest 기본 /tmp 실행은 pytest 자체 retention 대상이므로 전체 잔여물 보존을 주장하지 않는다.
이전 보고서/증거/소스는 그대로다. 새 기록·바이너리는 Linux 전용 연구 공간에 유지한다.

sudo/root/관리자 승격, 설정 변경, 서비스·WSL 종료/재시작, account/cgroup 작업,
Docker, 실제 HOST/차량/payload, 원격 push/PR/upload는 없었다.
현재 user-manager 권한을 실제 provider 승인으로 사용하지 않았다.

## 재실행

새 ABSENT basetemp/log 경로를 선택해 아래를 실행한다.
기존 basetemp를 재사용하면 pytest가 지울 수 있으므로 기존 evidence 경로는 지정하지 않는다.

~~~text
wsl.exe --distribution Ubuntu-24.04 --exec /usr/bin/python3 -I -B -
.venv/bin/python -m pytest -q tests/test_worker_entry.py --basetemp=<new-private-path>
.venv/bin/python -m pytest -q --cov=native_e_lab --cov-branch --cov-fail-under=90 --basetemp=<another-new-path>
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src/native_e_lab
.venv/bin/python -m build --no-isolation --outdir <new-build-output>
~~~

제품 tests는 별도 product checkout에서 기존 harness venv와 product/src PYTHONPATH를 사용한다.
명령·exit·제한된 출력과 UBSan runner는 전달 logs에 보존한다.
원본 branch들은 이동시키지 않았고 새 branch의 로컬 append-only commit만 생성한다.
최종 SHA/CLEAN/bundle hash는 별도 FINAL_DELIVERY.json에 기록한다.

## 프로젝트 상태와 다음 작업 하나

provider_registration=UNBOUND. 필수16증거 모두 UNAVAILABLE, available0.
application_authorized, build_execution_allowed, candidate_generation_allowed,
device_class_qualified, owner_proposal_allowed, policy_adopted, promotion_authorized,
runtime_accepted, runtime_qualified는 모두 false.
actual_payload_released, cleanup_allowed, recovery_execution_authorized,
H_executed, HREQ004_qualified도 false다.
이번 허용된 synthetic worker 실행·신규 lab 자원 정리는 제품 payload/cleanup 권한과 구분한다.

**다음 작업은 기존 provisioning plan을 현재 F/E/W 통합 코드에 맞춘 관리자 변경 검토 묶음으로 확정하는 것이다.**
보호된 factory/code origin과 실제 cross-UID·cgroup 결합을 증명하려면 현재 금지된 권한·설정 경계가 필요하다.
따라서 실제 적용은 이 결과만으로 자동 진행하지 않는다.
