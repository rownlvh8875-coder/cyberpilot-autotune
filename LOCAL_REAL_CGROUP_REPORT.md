# LOCAL NATIVE E — 실제 cgroup2 lab 및 연속 후속 검증

STATUS: PASS_REAL_KERNEL_LABS_WITH_EPOCH_LIMITATION
작업 시작:2026-11-05 / 완료 기록:2026-11-06
기준 source:ed8b68a993ea90e3f55b4931e3393bab464fee42
실제 실험 runtime commit:19101cd0a825a0d40e700a6cb7047dc897a0c512
branch:research/native-e-real-cgroup
최종 문서 commit/CLEAN/hash는 FINAL_DELIVERY.json에 기록한다.

## 이번 묶음에서 끝낸 작업

**고정 native E 연구 경로를 실제 kernel cgroup2에 연결했고, 정상 수명 실험과 변조 차단 실험을 별도 unit에서 순차 완료했다.**
환경 조회만 반복한 단계가 아니다. source snapshot builder, gate, native adapter,
회귀·독립 리뷰 수정·실제 제한 실험·후속 negative 실험까지 사용자 추가 승인 왕복 없이 진행했다.

외부 systemd user-unit의 G는 검증 후 같은 PID에서 F로 exec한다.
F가 private synthetic M을 만들고 M이 E를 만들며 E가 새 D와 고정 W를 관리한다.

~~~mermaid
flowchart LR
  U["새 실제 user-unit / 외부 P"] --> G["G → 같은 PID의 F"]
  G --> M["private synthetic M"]
  M --> E["native E"]
  E --> D["E가 생성한 kernel D"]
  D --> W["CLONE_INTO_CGROUP 고정 W"]
~~~

P는 manager가 만든 외부 lab 범위다. E가 생성한 D나 F의 생성 시점 원본 custody라고 부르지 않는다.
F는 P를 한 번 열어 참조만 보유·전달·해제한다. P를 unlink하지 않는다.
E는 D 생성, 원본 W pidfd, 단일 D stop, 정확한 SIGKILL wait, D 제거를 담당한다.

## 구현 파일 / API

| 파일 | 기능 |
| --- | --- |
| research/real_cgroup/factory.c | rl_run_fixed(void), 원본 P 참조, 기존 private bus/NPG1 연결, native M/E wait |
| research/real_cgroup/scope.c | 현재 새 unit의 cgroup mapping·owner·type 검사, old launcher 미호출 |
| research/real_cgroup/normal.c | 고정 normal M/credential-shim 연결, runtime fault selector 없음 |
| research/real_cgroup/build.py | build_fixed_kit(), 실제 source snapshot compile·전후 동일성·fixed ELF/hash 검사 |
| research/real_cgroup/gate.py | GO의8초 절대 deadline·정확한 EOF, kernel limits/NNP/scope/source 검사, 원본 FD exec |
| research/real_cgroup/lab.py | run_fixed_real_lab(), no-arg 고정 unit factory·loaded 검증·원본 job 완료 |
| tests/test_real_cgroup.py | 실제 unit을 만들지 않는62개 controller/gate/build/native-default tests |
| REAL_CGROUP_DESIGN.md / REAL_CGROUP_REVIEW.md | 설계·독립 리뷰·수정 경계 |

top-level에 임의 command/path/PID/FD/unit/receipt를 넘기는 실행·복구 API를 만들지 않았다.
원래111개 source/test/report는 byte exact 보존했다. PLAN/PROGRESS는 append-only다.
제품 checkout4b77b31dd23010f2d2b394466d88b04a4a2720e2와
기존 harness9545d5422096fced078be1243cee98310499d25f는 수정하지 않았다.
현재 remote main이라고 가정하지 않았으며 push/merge/PR/기존 branch 변경은 하지 않았다.

## 실제 실험1 — 정상 kernel 수명

별도 private kit와 fresh random user-unit 하나만 사용했다.
source-bound runtime commit/CLEAN, namespace의 기존 lab unit0, fresh delegation을 확인했다.
기존 app.slice에는 cpu subtree가 없어 그 설정을 바꾸지 않고,
이미 cpu/memory/pids가 enabled인 **user-manager -.slice** 아래 새 unit을 선택했다.
이는 현재 user-manager namespace root이며 host root라는 뜻이 아니다.

| 항목 | 실제 관측 |
| --- | --- |
| RuntimeMax / TimeoutStop | 30s /5s, loaded 값 검증 |
| Memory / Swap / Tasks | 128MiB /0 /8 |
| CPU | 25%, 실제 cpu.max=25000 100000 |
| Delegate / NNP / Restart | yes /yes /no |
| actual memory.max | 134217728 |
| actual memory.swap.max / pids.max | 0 /8 |
| gate | 실제 cgroup limits·current scope·NoNewPrivs1/CapEff0·source/asset 검사 PASS |
| F exec | 원본 검증 ELF FD, 같은 PID. 추가 Python child 생성 없음 |
| kernel placement | CLONE_INTO_CGROUP 실제 요청/실행, D 멤버가 원본 W뿐이고 후손0 |
| stop / wait | 실제 cgroup.kill 및 원본 pidfd의 정확한 CLD_KILLED/SIGKILL |
| D | 원본 name/OFD·populated0 확인 후 제거, native protocol 완료 |
| M/E/W | respective original-parent wait, F가 E pidfd를 채택하지 않음 |
| P | F refs 해제. 외부 P 삭제는 F가 하지 않음 |
| unit | 원본 systemd-run job exit0, --collect 후 not-found |
| 전후 기존 상태 | manager identity/controller configuration/source 동일 |
| 결과 | PASS_REAL_CGROUP_POSITIVE |

actual build에는 FS/clone/kill interposition을 연결하지 않았다.
따라서 이전 regular-files cgroup simulation과 구분되는 실제 kernel 관측이다.
D 동작 횟수는 고정 source의 단일 경로와 완료 protocol에 결속된다.
모든 syscall을 별도 tracer로 계수했다는 의미는 아니다.

## 실제 후속 실험2 — 변조 asset 차단

첫 unit이 종료·수거됐고 active namespace0임을 확인한 뒤 **새 kit/새 unit**을 만들었다.
이 새 kit의 fixed-worker 끝에 비민감한 한 byte만 추가했다.
정상 실험의 kit나 source·과거 evidence를 변경하지 않았다.

결과:
- loaded/kernel bounds 확인 뒤 gate가 ASSET_DRIFT로 거부했다.
- gate_pass=false, worker_executed=false, native F 결과 없음.
- F/E/W/D 실행 전에 차단됐다.
- original job exit5는 이 negative 실험의 예상된 거부 결과다.
- unit은 수거됐고 전후 기존 controller/manager identity/source는 동일했다.
- PASS_REAL_SOURCE_DRIFT_BLOCKED.

실제 unit은 총2개이며 서로 겹치지 않았다. native W 실행은 정상 실험의1개다.
같은 실패를 재적용하거나 이전 unit/old D에 다시 붙어 정리하지 않았다.

## 보존 결과와 WSL 세대 제한

각 실험의 before/after manager PID+starttime 및 관련 controller 설정은 일치했다.
두 실험 사이에도 controller configuration과 source는 일치했다.
단, 서로 다른 WSL 호출 사이에는 **user-manager MainPID/starttime이 달랐다**.

이를 숨기거나 전체 구간 identity preservation PASS로 바꾸지 않았다.
첫 post 검증의 whole_serial_operating_preserved=false 기록을 그대로 보존했고,
별도 제한 진단에서 달라진 필드가 MainPID/starttime임을 확인했다.
원인=UNKNOWN_NOT_INVESTIGATED. 동일 namespace/세대의 연속 실행이라고 가정하지 않는다.
기존 서비스 start/restart/stop, WSL shutdown/terminate, linger/reload/재부팅 명령은 실행하지 않았다.
WSL 종료 원인 추적이나 기존 manager 복구는 수행하지 않았다.
허용된 비대화형 WSL 기동의 자동 서비스 시작과 명시적 서비스 명령은 구분한다.
그 자동 기동이 이번 identity 차이의 원인인지는 확인하지 않았다.
각 실제 실험의 증거는 해당 fresh attempt에만 결속된다.

최종 bounded lab-prefix 조회: matching unit0. 두 unit은 각 attempt 안에서 수거 확인.
다른 epoch의 과거 자원 상태를 현재 absence로 성공 승격하지 않는다.
과거 internal-D UNKNOWN 실험과 잔여물도 건드리지 않았다.

## 실제로 검증하지 않은 것

- inner M은 **synthetic**이다. 실제 관리자 factory/PID1의 E 생성 backend가 아니다.
- 새 user-unit의 NNP/자원 제한은 실제다. E/W UID/GID/cap/seal 변경은 기존 no-forward shim이다.
- 실제 cross-UID 보안·protected code/loader origin·F1 original custody·admission fence는 미검증이다.
- readonly mount/namespace containment·외부 writer/async drain은 미구현/미검증이다.
- mkdir/open 및 검사/kill/unlink 사이 trusted-single-owner 가정이 남는다.
- kernel D directory removal과 모든 비동기 kernel/외부 자원 drain을 같은 성공으로 부르지 않는다.
- SDK 내부 close는 여전히 UNAVAILABLE다. 전체 HOST cleanup CONFIRMED를 선언하지 않는다.

provider_registration=UNBOUND. 기존 필수16종은 전부 UNAVAILABLE/available0이다.
이번 kernel lab 증거는 별도로 보존하며 원래16종을 자동 충족 처리하지 않는다.
9개 admission flag와 actual_payload_released,cleanup_allowed,recovery_execution_authorized,
H_executed,HREQ004_qualified를 포함한14개 전부false다.
고정 합성 W의 실제 실행은 H/제품/차량 payload release가 아니다.

## 테스트 / 리뷰 / 실행 환경

| 검증 | 결과 |
| --- | --- |
| CPU/POSIX 전체 연구 | **586 PASS /0FAIL/0SKIP** = 이전524 + 신규62 |
| 신규62 subset | PASS, 실제 unit 생성 없음 |
| 기존 Python coverage | 91.74%, threshold90 유지 |
| 새 adapter Python coverage | 91.04%, threshold90 유지 |
| native build | GCC -std=c11 -O2 -Wall -Wextra -Werror PASS |
| Ruff / format | exit0 /exit0,70Python files |
| mypy | 기존+신규14modules PASS, type/import ignores로 우회하지 않음 |
| 실제 kernel experiments | positive PASS1 + expected-denial PASS1, CPU 합계에 더하지 않음 |
| 새 native C coverage / sanitizer | 이번 UNAVAILABLE/NOT_RUN; 실제 실험은 unwrapped build |
| 기존 제품2786PASS | 이번 NOT_RERUN, unchanged, fresh 합계에 포함하지 않음 |
| old111 files | SHA256 일치, old refs 보존 |
| 원격 게시 | NONE |

관측 환경은 Ubuntu-24.04 WSL2, Linux6.18.33.2-microsoft-standard-WSL2/x86_64,
systemd255.4-1ubuntu8.18, 직접 EUID1000/CapEff0였다.
각 실제 attempt에서는 loaded property·actual kernel interface를 다시 확인했다.
세대가 같다고 가정하지 않았다. 새로운 패키지·venv dependency 설치도 하지 않았다.

독립 source review는 Important3/Minor1을 보고했다.
컴파일 후 변경 source를 새 pins로 묶는 오류, communicate 안 unknown close 재시도,
GO trailing/duplicate/EOF 공백을 모두 RED로 재현한 뒤 수정했다.
FIFO blocking도 전용 fixture의1초 alarm으로 RED 확인 후 NONBLOCK/type 검사로 수정했다.
source는 snapshot에서 실제 compile하고 original/snapshot 전후 동일성을 확인한다.
communicate 이후 pipe close는 그 경로만 소유하며 unknown이면 original job/stream을 보존한다.
GO는 단일8초 deadline과 정확한 EOF를 요구한다.
mypy가 지적한 read1 interface는 실제 buffer type 검사로 해결했다.

초기 mypy package 경로와 coverage78.82% 미달 기록도 보존했다.
namespace module search를 정확히 설정하고 필요한 실패 검사를 추가해 기준90을 통과했다.
검사 기준을 낮추거나 기존 테스트를 삭제하지 않았다.
수정 이후 독립 재리뷰/C0/I0는 선언하지 않는다. 최종 자료는 author 검증이다.

## 재실행 및 최종 인계

~~~text
.venv/bin/python -m pytest -q --cov=native_e_lab --cov-branch --cov-fail-under=90 --basetemp=<fresh-path>
.venv/bin/python -m pytest -q tests/test_real_cgroup.py --cov=research.real_cgroup --cov-branch --cov-fail-under=90 --basetemp=<another-fresh-path>
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
MYPYPATH=src:. .venv/bin/python -m mypy --explicit-package-bases -p native_e_lab -p research.real_cgroup -m research.admin_review.check_bundle
~~~

실제 lab은 scope가 이미 승인된 환경에서만 새 attempt로 실행한다.
전달 runner는 runtime commit을 정확히 요구한다. receipt/unit명/숫자FD로 재개·정리하지 않는다.
private raw unit/kit/PID 기록은 Git에 넣지 않았다. public evidence는 hash/상태/제한값만 담는다.
local append-only commit과 bundle만 만들며 push/PR/merge는 하지 않는다.

원래 요청의 필요한 환경 확인→연구 구현→자동 회귀→조건부 실제 합성 실험→후속 변조 검사까지 완료했다.
실제 provider/보호된 관리자 factory·cross-UID 적용은 현재 금지된 권한·설정 변경 경계라 실행하지 않았다.
단순 metadata 조회를 추가하거나 실행 자격 boolean을 만드는 작업으로 대체하지 않는다.
다음 작업 하나는 **보호된 관리자 factory/F1 및 cross-UID 적용 범위의 별도 구현·검증 계약 확정**이다.
이는 현재 연구 prototype의 kernel lab PASS를 HOST/runtime 자격으로 승격시키는 승인이 아니다.
