# LOCAL_NATIVE_E_FINAL_REPORT

2026-11-05 / 로컬 연구 작업. 상태: **RESEARCH_PROTOTYPE_VERIFIED_WITH_LIMITATIONS**.

이 노트북에서 별도 native E 연구 harness, 자동 테스트, 제한된 실제 Linux 합성 실험을 완료했다.
제품 provider 통합과 내부 D custody는 구현하지 않았다. 실제 HOST/runtime·차량 실행 자격은 부여하지 않는다.
제품 source/architecture guard/PR8·9는 변경하지 않았으며 원격 push·merge·외부 업로드는 하지 않았다.

## 1. 소스와 환경

| 항목 | 직접 관측 |
| --- | --- |
| 제품 clone | cyberpilot-autotune, main, 4b77b31dd23010f2d2b394466d88b04a4a2720e2, CLEAN |
| 연구 branch | research/native-e-local, 새 독립 Git 저장소 |
| 최종 실행·테스트 code revision | b9624850cdb98c75f29dac0d3b4239ea3c3d4d92 |
| 독립 whole-change review revision | 200b4f900a5512de9ff6d30fbd9704fe551955c1 |
| Windows 진입 | 비관리자 네이티브 PowerShell에서 wsl.exe --distribution Ubuntu-24.04 --exec 사용 |
| Linux | Ubuntu-24.04 WSL2, 6.18.33.2-microsoft-standard-WSL2, x86_64 |
| 실행 주체 | EUID1000 / EGID1000 / CapEff=0000000000000000 |
| Python / compiler | Python3.12.3 / Ubuntu GCC13.3.0 |
| systemd | 현재 UID user bus 조회255.4-1ubuntu8.18 |
| user-manager 설정 출처 | 이전 보고서 보존. 지정3파일의 로컬 dpkg MD5 비교를 이번에1회 수행, 3MATCH |
| 비공개 HF 참고 | 정상 인증 미확인으로 UNAVAILABLE_AUTH. 읽거나 원본 구현으로 재현했다고 주장하지 않음 |

과거599236a6를 현재 main으로 가정하지 않았다. 기존 Windows 작업 폴더는 다른 저장소이므로 수정하지 않고
Linux의 새 전용 workspace에 제품 clone과 연구 harness를 분리했다.
기존 preflight 보고서3개의 SHA256은 재확인해 모두 동일했다.
패키지 DB 일치는 배포판 진위·관리자 E 승인·원본 custody의 인증이 아니다.
이전 조회와 같은 namespace/세대 또는 지속 실행이라고 가정하지 않았다.
WSL shutdown/terminate를 실행하지 않았으며 과거 Stopped 원인은 계속 UNKNOWN이다.

제품 guard가 기존 successor 경로를 엄격히 고정하고, 기존 executor도 클라우드 도구 SHA/경로에 고정돼 있었다.
guard를 넓히거나 제품과 bridge를 만들지 않고 독립 연구 harness를 선택했다.

## 2. 구현 파일과 API

| 파일 | 구현 |
| --- | --- |
| src/native_e_lab/runner.py | 인자 없는 run_fixed()와 수동 Observation. 임의 명령/경로/PID/FD/unit/receipt 실행 API 없음 |
| src/native_e_lab/supervisor.c | E가 sealed 고정 memfd·socketpair를 만들고 clone3(CLONE_PIDFD)로 고정 worker와 원본 pidfd를 원자적으로 보유 |
| src/native_e_lab/protocol.py | 최대512byte length framing, 명확한 EOF, cohort/generation/nonce/sequence/stage, ancillary FD 거부·정리 |
| src/native_e_lab/handles.py | factory-only live handles, 직렬화/복사 금지, 원본 OFD anchor 보유, 자기 프로세스 kcmp(KCMP_FILE) 비교 |
| src/native_e_lab/lab.py / gate.py | 새 factory user-unit만 실행, manager·커널 상한 검증 전 worker 차단, 원래 job/pipe만 관리 |
| src/native_e_lab/build_native.py | 고정 C source만 로컬 compiler로 빌드, binary SHA sidecar 작성 |
| tests/ | protocol·native·소유/정리·lab gate·review repair 회귀 |
| PLAN.md / PROGRESS.md | 단일 실행 계획과 진행/결정/검증 이력 |
| REVIEW.md / COMMANDS.md / evidence.json | 리뷰 경계, 실제 명령·exit 및 제한된 증거 |

실행 단계는 BIND→OWNED→RUN→DONE→COMPLETE이고, RUN 뒤 정확한 송신 EOF가 필요하다.
callback·receipt 생성 또는 숫자 FD는 실행 단계나 정리 권한이 아니다.
잘못된 context/순서, 중복·추가·빈·초과·부분 frame와 SCM_RIGHTS는 거부한다.
worker는 고정된 작은 합성 상수만 처리하며 host directory FD·환경 시크릿·네트워크 자격증명을 받지 않는다.
standard streams는 null, worker FD는 자신의 socket·sealed memfd만 유지한다.

E가 만든 원본 pidfd로만 직접 자식에게 signal/wait한다. 숫자 PID·unit명·과거 receipt로 재접속하지 않는다.
wait/close 불확실성은 UNKNOWN으로 유지하며 재시도하지 않는다. 알 수 없는 pipe object는 격리 보유한다.
unknown kernel/close 값을 false·0으로 채우지 않고, supervisor exit와 실제 worker exit도 구분한다.
호스트·protocol 오류는 관측값과 거부로 남으며 승인 플래그를 만들지 않는다.

## 3. TDD와 검증 결과

초기 모듈/binary 부재 RED 뒤 구현했으며, 실제 결함들은 별도의 실패 테스트로 재현했다.
factory 실패 정리 누락, 취소 masking, 불확실 close의 성공 승격, supervisor/worker exit 혼동,
실행 후 timeout의 미실행 오기, 같은 디렉터리 재open의 외부 FD close를 수정했다.
실패 주입은 tests/의 fake 또는 test-only linker wrapper에 있고 production fault switch는 없다.

| 검증 | 실제 결과 |
| --- | --- |
| 연구 전체 pytest + branch coverage + fail-under90 | **123PASS / 0FAIL / 0SKIP**, exit0 |
| 기존 제품 전체 회귀, 수정 후 재실행 | **2786PASS / 0FAIL / 0SKIP**, exit0 |
| 고유 테스트 합계 | 2909. 중간 재실행·계측13개는 추가하지 않음 |
| 연구 Python coverage | **92.68%**, statements488 / missing27 / branches140, exclusion으로 기준을 낮추지 않음 |
| 제품 coverage | **98.50%**, 기준90 유지 |
| 기존 safety / residual / replay | 100% / 97.85% / 98.48%, 각 기준95 유지 |
| 연구 ruff / format / mypy | exit0, source7files type check |
| 제품 ruff / format / mypy | exit0, source75files type check |
| 제품 golden replay verify-all | exit0, 4fixtures |
| C -std=c11 -O2 -Wall -Wextra -Werror | exit0 |
| 제품/연구 sdist·wheel | 전용 venv의 build --no-isolation에서 exit0 |
| 새 깨끗한 wheel venv 설치·native 재빌드·고정 worker smoke | 모두 exit0 |
| C 계측 복사본, 기존 native13개 | 13PASS, line82.35%, branches executed78.41%, taken51.70% |

첫 python -m venv와 기본 python -m build는 ensurepip 부재로 실패했다.
sudo/apt 설치 없이 새 venv를 --without-pip으로 만들고 기존 번들 pip Python 코드로만 bootstrap했다.
프로젝트 dev/research/build 의존성은 이 전용 venv에 설치했다.
기본 build 격리 경로의 실패는 그대로 기록했으며, --no-isolation은 이미 독립된 새 venv에서 실행한 대안이다.

Python coverage는 native C·커널 전체를 계측한 수치가 아니다. C 계측은 명시한13개에 한정되며,
test-only linker failure wrapper 전체의 C branch coverage나 모든 비동기 signal 순간을 증명하지 않는다.
실제 fixed-child/EOF/timeout/비정상 종료/FD 전달 검증과 pure fake의 취소·정리 경로 검증은 구분한다.
PASS 수는 기대한 거부·UNKNOWN 처리 테스트도 포함하며 성공한 제품 payload 실행 수가 아니다.

## 4. 실제 OS 합성 실험

user-level unit 실험은 총2회이며 동시 활성은1개였다.
첫 실험은 초기 구현에서 성공했지만 동시 source manifest가 없어 최종 revision 증거로 승격하지 않았다.
두 번째는 CLEAN code revision b962485에서 새 factory unit을 만들고 source/test 해시를 전후 대조했다.

| 최종 unit 검증 | 값 / 결과 |
| --- | --- |
| RuntimeMaxSec / TimeoutStopSec | 30s / 5s |
| MemoryMax / MemorySwapMax | 134217728 / 0 |
| TasksMax / CPUQuota | 8 / 25% |
| 실제 kernel memory.max / memory.swap.max | 134217728 / 0 |
| 실제 kernel pids.max / cpu.max | 8 / 25000 100000 |
| worker 실행 전 gate | manager6속성 및 kernel4제어값 모두 일치 후 실행 |
| 실제 고정 worker / E / 원래 job exit | 0 / 0 / 0 |
| 정상 경로 정리 | CONFIRMED, recorder/provider/H 실행 아님 |
| 종료 뒤 해당 새 unit 읽기 | LoadState=not-found, ActiveState=inactive, exit0 |
| source/test pins | 전후 동일 |
| 원본 directory OFD 보강 | 같은-process kcmp 조회 성공, 원본 dup는 SAME / 별도 reopen은 DIFFERENT |

audit observer는 이 호출에서 생성한 정확한 unit명만 메모리에 식별해 종료 후 읽기 조회에 사용했다.
이 이름은 stop/recovery 권한으로 사용하거나 보고서에 게시하지 않았다.
기존 unit의 start/stop/restart나 user-manager 종료는 하지 않았다.
이 상한은 작은 실험의 운영 제한이며 H profile·차량 임계값·실행 자격이 아니다.
C의 per-process rlimit와 외부 unit의 aggregate 제한도 구분한다.

## 5. 리뷰와 수정 범위

fresh 독립 whole-change review1회가200b4f9 전체 code/tests/docs를 읽고 pure 재현으로 P2세 가지를 보고했다.

1. lab pipe close가 원래 취소를 가리고 나머지 pipe 정리를 건너뜀.
2. socket close 중 BaseException 뒤 finalizer가 불확실한 FD close를 재시도할 수 있음.
3. gate가 clone3 미생성을 worker 실행으로 보고함.

세 가지 모두 RED→수정→전체123개 GREEN으로 검증했다.
검토자는 metadata-only 디렉터리 OFD 구별의 한계도 확인했다.
추가로 원본 anchor와 kcmp를 구현했고 같은 디렉터리의 다른 OFD reopen 거부,
비교 권한/가용성 부재 시 UNKNOWN·무fallback을 테스트했다.
**이 수정들과 OFD 보강은 구현자 self-review/재검증이며 독립 C0/I0로 표시하지 않는다.**
최종 전체 테스트·정적 검사·새 wheel smoke·revision에 바인딩한 실제 unit 검증을 마쳤다.

## 6. 자원·정리·보존

- 최종 실제 unit은 종료 뒤 not-found를 관측했다. 완료한 job/worker의 원래 handle로 정상 종료를 확인했다.
  전체 시스템에 잔여 process가 전혀 없다는 주장은 하지 않는다. 전체 시스템 PID 탐색은 하지 않았다.
- 고의 FD 상실·이름 교체·부분 정리 테스트가 남긴 private fixture는 **69디렉터리 / 14파일 / 총112byte 파일 내용**이다.
  모두 새 harness의 lab-fixtures 범위이며 기존 사용자/차량 데이터가 아니다.
  잃은 소유권을 오래된 경로/receipt로 복구해 자동 삭제하지 않았다.
- 불확실 FD/pipe 테스트의 retained descriptor/object는 그 테스트 프로세스 종료까지 남겼다.
  이를 원래 close 성공으로 바꾸지 않았다. 정상 최종 실험의 CONFIRMED와 별개다.
- source·venv·wheel·빌드·logs·Git history는 새 workspace에 연구 결과로 남긴다.
  상세 로그는 로컬 logs/에 있고 Git bundle/원격에 넣지 않았다.
- 제품 clone은 끝까지 같은4b77b31d / CLEAN. 이전 보고서3개 hash도 동일.
- Windows/WSL 전역 설정·권한 상승·시스템 설치/업데이트·재부팅·기존 service 조작·
  기존 cgroup controller/프로세스 직접 쓰기·Docker·SSH/방화벽·차량·실제 driving data 작업은 하지 않았다.
  WSL 기동과 새 합성 unit의 정상 systemd runtime 동작은 명시적으로 승인된 범위였다.

인계 commit 뒤 최종 branch/HEAD/CLEAN 상태는 logs/final-state.json에 실제 조회값으로 기록한다.
소스 검증 대상 revision과 report-only 인계 commit은 구분한다. 원격 push/PR 변경은0회다.

## 7. 완료·부분 완료·미검증

완료한 범위는 별도 연구 코드, 반복 가능한 자동 테스트, 고정 직접 자식과 실제 제한 unit의 작은 실험,
원본 pidfd·sealed memfd·socket/OFD anchor의 제한된 수명주기 검증이다.

**미구현/미검증:** E가 생성 시점부터 직접 보유하는 내부 cgroup D, E가 정지할 D 바깥에 있다는 binding,
atomic directory custody/admission fence, namespace containment, 실제 read-only mount,
aggregate descendant 원본 custody, 외부 writer/async drain, host crash/recovery, 제품 provider 통합.
systemd가 만든 외부 unit을 E가 원래 만든 내부 D라고 부르지 않는다.

fstat만으로 원본 OFD를 증명하지 않는다. 추가 kcmp도 자기 프로세스의 신뢰된 owner 경로에 한정된다.
동일 UID의 적대적 code, 동시 FD-table mutation/alias·generation race, 이름 lstat→rmdir 경쟁을
방어하는 보안 경계는 아니다. 그런 일반적인 no-foreign-close·전체 custody 자격은 미증명이다.
연구 prototype 완료를 native E 전체 qualification 또는 실차 readiness로 과장하지 않는다.

## 8. 유지되는 프로젝트 상태

provider_registration = **UNBOUND**.
기존 필수16증거 = **UNAVAILABLE**, 자동 충족 처리0개.

아래14개는 모두 false다. 새 qualification/admission 레코드를 만들지 않았다.

application_authorized, build_execution_allowed, candidate_generation_allowed,
device_class_qualified, owner_proposal_allowed, policy_adopted, promotion_authorized,
runtime_accepted, runtime_qualified, actual_payload_released, cleanup_allowed,
recovery_execution_authorized, H_executed, HREQ004_qualified.

이번에 허용된 lab build/합성 worker 실행과 프로젝트 실제 H/제품/차량 payload를 구분한다.
run_fixed Observation을 직렬화·위조·재생해도 실행/정리 authority를 얻을 API는 없다.

## 9. 재실행과 다음 작업

재실행 명령은 README.md, 실제 명령과 실패/성공은 COMMANDS.md를 따른다.
새 writable venv에 dev 의존성을 설치하고 build_native→pytest/coverage→ruff/format/mypy→build 순서다.
unit 실험은 독립적 명시 호출이며 기존 서비스·과거 unit명에 다시 붙지 않는다.
raw 사용자 데이터나 secret이 필요하지 않다.

**다음 작업 하나:** E가 생성 시점부터 내부 D를 보유하고, E 자신은 그 D 바깥에 머무르며
D를 정지·회수하는 Linux custody 경계를 설계·구현하는 별도 후속 연구.
이유: 현재 검증된 원본 직접 자식 handle과 외부 systemd unit은 그 내부 D 증명이 아니기 때문이다.
