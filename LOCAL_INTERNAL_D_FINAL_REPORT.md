# LOCAL_INTERNAL_D_FINAL_REPORT

2026-11-05. **TRUSTED_LAB_INTERNAL_D_LIFECYCLE_PASS**。
신뢰된 단일-owner 연구 범위에서 E의 내부 D 생성→worker admission→정지→회수를 구현하고 실제 커널에서 검증했다.
전체 native provider/custody 자격·제품 통합·차량 readiness는 부여하지 않는다.

## 소스·보존·환경

| 항목 | 실제 값 |
| --- | --- |
| 연구 base | 9545d5422096fced078be1243cee98310499d25f |
| 새 branch | research/native-e-internal-d, 별도 Linux worktree |
| 최종 실제 실행 runtime code | 385b0e1b0598659bf20da37d83d8c5e20c89c433 |
| 독립 전체 변경 리뷰 | 9545d54..3f72de3387b0a0f0fd71b897f07e25b1ac0e5512 |
| 제품 reference | 4b77b31dd23010f2d2b394466d88b04a4a2720e2, main/CLEAN |
| 원래 연구 branch | research/native-e-local /9545d54/CLEAN 유지 |
| 실행 환경 | Ubuntu-24.04 WSL2, Linux6.18.33.2-microsoft-standard-WSL2/x86_64 |
| 현재 주체 | EUID1000, EGID1000, CapEff=0000000000000000 |
| 원격 작업 | push/merge/PR 변경/외부 업로드 없음 |

기존 LOCAL_NATIVE_E_FINAL_REPORT.md와 evidence.json은 byte 변경 없이 보존했다.
단일 PLAN.md와 PROGRESS.md에 후속 단계를 추가했다. 이전 systemd3파일 출처 검사는 반복하지 않았다.
과거 WSL namespace/세대와 동일하다고 가정하지 않았고 비공개 자료의 접근을 새로 주장하지 않았다.
Windows/WSL 전역 설정·sudo·시스템 설치·기존 서비스 start/stop/restart·
기존 cgroup controller 변경/프로세스 이동·Docker·차량·Params 작업은 하지 않았다.
Git worktree 등록과 새 연구 branch의 append-only 로컬 commit만 사용했다.

## 구현과 경계

공개 API는 인자 없는 native_e_lab.domain.run_domain_lab()이다.
호출자가 임의 명령·경로·PID·FD·unit·receipt를 전달해 실행/정리하는 API는 없다.

| 파일 | 역할 |
| --- | --- |
| domain_supervisor.c | E가 새 D를 직접 생성, 원본 directory FD/anchor 보유, born-in-D 원본 pidfd 생성 및 정지/회수 |
| domain_worker.c | 임의 payload 없는 고정 합성 worker 실행 이미지 |
| domain.py | 고정 바이너리 binding, bounded protocol, 수동 DomainObservation |
| domain_gate.py | 새 외부 scope·kernel limits 검증 전 native 실행 차단 |
| lab.py | 고정 새 transient unit 생성, Delegate=yes와 기존6상한 검증, 실패 context 보존 |
| build_native.py | 고정 C source3개만 빌드 |
| tests/test_domain*.py | native helper·protocol/control·review·write-fault 회귀 |
| INTERNAL_D_DESIGN.md / INTERNAL_D_REVIEW.md | 설계와 독립/수정 검증 경계 |

systemd가 만든 unit은 외부 실험 scope다. **내부 D는 그 안에서 E가 mkdirat로 만든 별도의 새 cgroup**이다.
E는 D 밖에 머문다. clone3(CLONE_INTO_CGROUP|CLONE_PIDFD)로 worker를 D 안에서 태어나게 하며
기존 프로세스를 cgroup.procs 쓰기로 이동하지 않는다. 원래 pidfd는 생성 syscall에서 보유한다.

E의 birth trampoline은 고정 worker ELF를 보유한 executable FD로 execveat한다.
CLOEXEC에 의해 directory FD는 새 worker 이미지가 시작되기 전에 닫힌다.
E는 원래 child pidfd를 유지한 상태에서 실행 이미지 identity와 FD0..4/no-directory 상태를 검증한 뒤 RUN을 보낸다.
worker에는 자신의 socket·sealed 합성 memfd·null 표준 스트림만 남고 환경은 LANG만 전달된다.
임의 binary/payload 선택이나 host directory FD·시크릿·네트워크 자격증명 전달 경로는 없다.
이는 native trampoline 전체의 namespace 격리 증명은 아니다.

정지 직전 원본 D binding, E의 외부 membership, 보유한 worker만의 직접 membership,
하위/소멸 중 cgroup 수0을 확인한다. 관측 실패나 알 수 없는 subtree는 terminal UNKNOWN이다.
원본 D FD 기준 cgroup.kill을 한 번만 쓰고 원본 pidfd를 한 번만 wait한다.
CLD_KILLED/SIGKILL을 검사하며 정상 exit137과 구별한다.
populated0과 원본 binding 검증 후 자기 D를 제거한다.
실패한 D의 이름/숫자 FD/PID/receipt로 다시 붙지 않는다.

cgroup.kill은 하위 cgroup에도 영향을 주므로, 알 수 없는 subtree를 감지하면 정지를 거부하도록 했다.
populated는 subtree의 live process 유무를 나타낸다.
인터페이스 근거: [Linux kernel cgroup v2 문서](https://docs.kernel.org/admin-guide/cgroup-v2.html).
이 snapshot 검사는 외부 writer가 검사 이후 변경하는 것을 막는 admission fence가 아니다.

## 실제 제한 실험과 실패 이력

이 후속 작업에서 새 user-unit4개를 순차 실행했다. 동시 활성은1개였다.
이전 단계의 unit2회는 이 건수에 더하지 않는다.

| code revision | 결과 | native 정리 | 종료 뒤 외부 unit |
| --- | --- | --- | --- |
| 3f72de3 | 최초 D 수명주기 PASS | CONFIRMED | not-found/inactive |
| 5d7a520 | 리뷰 수정·고정 exec 이미지 PASS | CONFIRMED | not-found/inactive |
| b2f2d50 | 새 subtree 검사로 BLOCKED_GATE_OR_JOB | UNKNOWN, exit21 | not-found/inactive |
| 385b0e1 | kernel schema 수정, 새 cohort PASS | CONFIRMED | not-found/inactive |

b2f2d50 실패는 삭제/승격하지 않았다. 그 D에는 재접속하거나 native cleanup을 재시도하지 않았다.
그 뒤의 정상 외부 scope teardown과 새 cohort의 성공은 이전 native UNKNOWN의 해결 증명이 아니다.

읽기 전용 현재-self 진단에서 cgroup.stat380byte와 interleaved nr_subsys_* 필드를 확인했다.
256byte·인접 필드 sscanf 가정 때문에 새 guard가 차단했던 것이다.
원인 재현 후 4KiB bounded key parser로 수정했다.
필수 두 counter가 모두 정확히0이어야 하며 누락·중복·음수·초과 입력은 거부한다.
512byte protocol framing, runtime caps와 합격 임계값은 낮추지 않았다.

| 최종 실제385b0e1 검증 | 관측 |
| --- | --- |
| RuntimeMaxSec / TimeoutStopSec | 30s /5s |
| MemoryMax / MemorySwapMax | 134217728 /0 |
| TasksMax / CPUQuota | 8 /25% |
| loaded delegation | yes |
| 실제 memory.max / memory.swap.max | 134217728 /0 |
| 실제 pids.max / cpu.max | 8 /25000 100000 |
| E가 새 D 생성·원본 OFD 유지 | PASS |
| worker born-in-D / E outside | PASS /PASS |
| 고정 실행 이미지·worker entry no-directory FD | PASS |
| 원본 D로 live worker 정지 | PASS |
| 원본 waitid | 정확한 SIGKILL, worker137/E0/job0 |
| populated0 / 원본 D 제거 | PASS /PASS |
| 종료 뒤 해당 새 외부 unit | LoadState=not-found, ActiveState=inactive, 조회exit0 |
| source/test pins | 실제 실험 전후 동일 |

새 unit 이름은 원래 생성 호출의 audit observer에서만 메모리로 추적해 종료 후 읽기 조회했다.
그 이름을 정리/복구 권한으로 쓰지 않았으며 공개 결과에 포함하지 않았다.

## 테스트·정적 검사·빌드

| 검증 | 최종 결과 |
| --- | --- |
| 연구 전체 | **178PASS /0FAIL /0SKIP**, exit0 |
| 이전 연구 회귀 | 123개 포함, 반복 가산 없음 |
| 이번 새 고유 사례 | 55개 |
| 기존 제품 전체 회귀 | **2786PASS /0FAIL /0SKIP**, exit0 |
| 고유 합계 | 2964, 실제 unit·반복 검사 미가산 |
| 연구 Python branch 포함 coverage | **91.74%**, 기준90 유지 |
| 기존 제품 coverage | **98.50%**, 기준90 유지 |
| Ruff / format / mypy | exit0, Python source9modules |
| Native compiler | 고정 ELF3개, -std=c11 -O2 -Wall -Wextra -Werror, exit0 |
| sdist/wheel build | 전용 venv build --no-isolation, exit0 |
| 새 wheel venv install/native build/smoke | 모두 exit0 |

coverage는 Python668statements/204branches를 대상으로 한다. C/커널 전체 coverage 수치는 미계측이다.
native helper fixture는 일반 private filesystem에서 실행하며 실제 cgroup 제어로 표현하지 않는다.
정상 exit137/SIGKILL 구별 fixture는 고정 직접 자식의 실제 pidfd/waitid를 사용한다.
partial/unknown-after-write fixture는 실제 C write block과 cleanup tail을 regular file에 실행해
한 번만 쓰고 exit21·D 잔존을 확인했다. 실제 cgroup.kill의 오류를 OS에서 강제로 유발한 증거는 아니다.

fresh wheel smoke는 direct fixed worker의 정상 완료와
검토된 새 scope 밖에서 domain 실행이 UNAVAILABLE 경로로 거부됨을 확인한다.
wheel 자체를 별도 실제 D 실험 unit에서 다시 실행한 것은 아니다.

최종 실제 실험385b0e1 뒤 runtime source는 변경하지 않았다.
이후2개의 write-fault 테스트만 추가해 전체178개를 재검증했다.
실제 실험의 기존 source/test pins는 그대로이고, 새 테스트 추가는 별도로 기록했다.

중간 coverage89.99%는 기준 미달로 취급했고 기준을 낮추지 않았다.
native fixture 작성 중 문자열/oversize fixture 오류도 수정했다. 최종 PASS에 실패 실행을 덧셈하지 않는다.

## 리뷰와 명령 기록

독립 전체 변경 리뷰1회는3f72de3를 검토했다.
P2두 건: 실패 binding/membership의 정리 성공 승격, readdir 오류의 정상 EOF 오인.
P3한 건: 정수137의 정확한 signal 종류 소실.
모두 native fixture에서 3RED/1positive-control로 재현 후 수정했다.
리뷰 이후의 exec 경계·subtree/schema 보강과 최종 수정은 작성자 self-review/재검증이다.
**최종 source를 독립 C0/I0로 표시하지 않는다.**

실제 주요 명령과 exit:
- git worktree add -b research/native-e-internal-d ... 9545d54:0.
- python3 -m venv --without-pip; 기존 venv pip --python <새 venv> install -e .[dev]:0.
- pytest baseline:123PASS/0; 새 contract RED:8FAIL/1; review RED:3FAIL/1positive; kernel-shape RED:1FAIL.
- python -m native_e_lab.build_native:0.
- python -m pytest -q --cov=native_e_lab --cov-branch --cov-report=term-missing --cov-fail-under=90:최종0/178PASS.
- 기존 제품 pytest --cov=cyberpilot_autotune --cov-fail-under=90:0/2786PASS.
- python -m ruff check .; ruff format --check .; mypy src/native_e_lab:각0.
- python -m build --no-isolation; 새 venv wheel install/native build:각0.
- 원본 job 기반 새 bounded systemd-run user-unit:4회, 위 표 결과.
- 현재-self cgroup.stat bounded 읽기:0. 실패 D에는 읽기/쓰기 재접속0회.
- sudo/daemon-reload/기존 서비스 조작/프로세스 이동/WSL shutdown/차량·Docker 작업:0회.

상세 제한 로그는 로컬 logs/에 보존한다. HF 인증·로그인·외부 토큰·개인 파일 조회는 하지 않았다.

## 잔여 자원·한계·다음 작업

최종 D 제거와 외부 unit 회수는 확인했다.
이전 실패 D의 native 정리 상태는 계속 UNKNOWN이다. 전체 시스템에 residue가 전혀 없다고 주장하지 않는다.
새 작업공간의 handle-loss private filesystem fixture와 venv/build/logs는 보존한다.
오래된 경로/receipt로 잃은 소유권을 복구해 일괄 삭제하지 않았다.
원래 연구 branch/제품 source는 CLEAN이며 이전 report/evidence bytes도 유지했다.

미증명: mkdirat→openat 사이 원자적인 생성시점 custody, 같은 UID 적대적 writer에 대한 admission fence,
membership·이름 변경 race 차단, unlink 원자적 이름 binding, namespace containment,
실제 readonly mount, 외부 writer/async drain, crash recovery와 실제 provider 통합.
systemd 외부 unit을 E가 만든 D로 승격하지 않으며 W_OK/Delegate=yes를 자격으로 쓰지 않는다.

프로젝트 상태: **UNBOUND**, 필수16증거 **UNAVAILABLE**.
application_authorized, build_execution_allowed, candidate_generation_allowed,
device_class_qualified, owner_proposal_allowed, policy_adopted, promotion_authorized,
runtime_accepted, runtime_qualified, actual_payload_released, cleanup_allowed,
recovery_execution_authorized, H_executed, HREQ004_qualified는 전부 false다.
이번 승인된 lab build/고정 합성 worker/D stop과 실제 H·제품 payload 승인은 별개다.

재실행: 새 전용 venv에서 build_native→pytest/coverage→ruff/format/mypy→build,
새 unit의 명시적 실행은 python -I -B -c 'from native_e_lab.domain import run_domain_lab; print(run_domain_lab())'.
기존 unit·과거 receipt에 붙지 않으며 source/capability 불확실 시 새 실험을 자동 반복하지 않는다.

**다음 작업 하나:** 내부 D admission fence와 원본 custody 규약을 설계해,
관측 이후 외부 writer가 이름·membership을 바꿀 수 있는 경계를 다룬다.
현재 snapshot·신뢰된 단일-owner 실험이 그 보안을 증명하지 않기 때문이다.
