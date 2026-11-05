# Native E: 최소 host-principal provisioning / rollback 계획

Status: PROPOSED / PLAN_ONLY / NOT_APPLY_READY  
Base: aadf62ff3d826ed432b412f18143d5fa1144d4ba  
Date: 2026-11-05  
상위 계약: [ADR-F1](ADMISSION_FENCE_CUSTODY_ADR.md). 이 문서는 별도 OS 변경 승인이 아니다.

## 1. 결정과 적용 제한

F는 host system manager와 고정 factory adapter로 구성한 신뢰 경계로 제안한다.
기존 PID1을 다시 시작하거나 기존 user-manager를 바꾸지 않는다.
새 비로그인 host 계정 두 개로 E와 W를 분리한다. F를 위한 새 root daemon·네트워크 endpoint는 만들지 않는다.
새 system-level 단일 실험 service P에서 E를 실행하고, E가 그 아래 D를 직접 mkdir/보유한다.
새 service의 P는 systemd-created이며 E-created D가 아니다.

최소안은 **E 초기 bootstrap에만 CAP_SETUID/CAP_SETGID**, credential seal 이후 E/W는
effective/permitted/inheritable/ambient capability0, W의 real/effective/saved/fs UID/GID는 W로 고정한다.
두 capability도 임의 UID/GID 전환 능력이므로 좁은 worker 전용 권한이라고 부르지 않는다.
추가 SYS_ADMIN/SYS_PTRACE/KILL/DAC_OVERRIDE/SETPCAP/file capability/setuid binary는 제안하지 않는다.
고정 native bootstrap의 인자 제한 seccomp와 원래 birth/handoff 검증을 먼저 구현·검토해야 한다.
현재 바이너리를 이 service로 실행하는 것은 금지하며, 이 계획만으로 install/start할 수 없다.

다른 host UID와 mode만으로 F1이 완성되지 않는다. root/manager는 TCB다.
TCB 밖의 동등한 privileged actor에 대한 방어, readonly mount, namespace containment,
외부 writer/async drain, H/provider/차량은 이번 최초 lab profile 범위가 아니다.
현재 환경에 해당 계정/정책이 존재하거나 필요한 권한이 있다는 관측도 하지 않았다.

## 2. 선택지와 비용

| 선택지 | 운영 변경 | 결정 |
| --- | --- | --- |
| 기존 UID1000 + user-manager | 적음 | 외부 동권한 writer 배제 불충분, 강한 fence로 불가 |
| F가 W 생성 후 E에 PID 전달 | 별도 privileged launcher | E의 직접 자식 birth/wait custody가 달라져 제외 |
| E에 지속적인 ptrace/kill/global admin | 큼 | 기존 검사를 억지로 유지하려고 권한 확대하지 않음 |
| system manager F + E/W 별도 static 계정 + 일시 credential caps | 계정2/새 service/보호 코드/새 bootstrap | 최초 검토 대상. 미구현 부분 때문에 적용 차단 |
| same-UID LSM 분리 | 정책/배포판 의존 | 가능한 별도 backend이나 이번 최소안에서 병행하지 않음 |

DynamicUser의 자동 UID 재활용은 이 최초안에 쓰지 않는다.
static 계정도 자동 재사용·삭제하지 않는다. 실패 cohort는 수동 기록만으로 다시 시작할 수 없다.

## 3. 권한과 process 배치

~~~mermaid
flowchart TD
  F["F: trusted system manager + fixed factory adapter"] --> P["new P: systemd-created, empty inner node"]
  P --> S[".supervisor: E outside D"]
  P --> D["D: E-created, original directory refs"]
  S --> B["E clone3 into D + original pidfd"]
  B --> W["W: distinct host UID, fixed worker, caps0"]
~~~

| 주체/단계 | credential와 권한 | 금지 |
| --- | --- | --- |
| F | 관리자/기존 system manager TCB. 이번 신규 P만 factory 생성 | 임의 command/PID/path/FD/unit 인자를 받는 API, 기존 service 조작 |
| E entry | cp-e-lab; bounding/ambient 초기 SETUID+SETGID만. untrusted 입력 없음 | 외부 payload 진입, 임의 UID0 전환, caller-writable loader/code |
| E pre-birth | 고정 syscall/credential policy 설치; E 전용 P 원본 grant; E가 D 생성 | policy 실패 후 clone, 기존 P/D attach |
| child pre-entry | D에 직접 태어남. groups 비움 → 모든 GID=W → 모든 UID=W → caps 모두 비움 → NNP/FD seal 검증 | saved E UID/GID, host directory/control FD, 일반 credentials 전달 |
| E runtime | E UID 유지, 네 capability set0; original D refs와 original pidfd | 광범위 ptrace/kill capability, pidfd 신호 권한 가정 |
| W runtime | W UID/GID, 부가 group0, 네 capability set0, 고정 ELF/고정 protocol | 임의 command, process 이동, fork tree, 외부 FD import |
| X | E/W 계정 외 비신뢰 actor | P/D mutation, E code/memory/FD 접근이 실제 OS에서 거부되어야 함 |

CapBnd에는 SETUID/SETGID가 남을 수 있다. CAP_SETPCAP 없이 bounding0을 주장하지 않는다.
permitted/inheritable/ambient/effective0 및 NoNewPrivileges의 실제 적용을 별도로 확인한다.
W UID로의 전환만 허용하는 argument-level filter가 필요하다. setuid/setreuid/setfsuid와
GID 변형 등 우회 syscall/비native ABI는 막고, 허용 setresuid/setresgid는 고정 숫자 세 인자만,
setgroups는 size0만 허용한다. 일반 systemd SystemCallFilter의 이름 목록을 인자 검사로 오인하지 않는다.
기존 binary에는 이 phase별 credential gate가 없다. 구현 전 OS 실행0.

## 4. 필요한 새 경로와 소유권

아래는 미래의 후보 경로다. 이번에 존재 여부 조사·생성·변경하지 않았다.
이미 어떤 경로/계정/unit이 존재하면 채택/overwrite하지 않고 충돌로 중단한다.

| 대상 | 미래 owner/mode | 목적·제약 |
| --- | --- | --- |
| cp-e-lab / cp-w-lab | 새 서로 다른 local system UID/GID, nologin, home 없음 | 실제 숫자는 관리자 allocator 결과 검증 후 고정; 추정 숫자 없음 |
| /etc/sysusers.d/cyberpilot-native-e-lab.conf | root:root 0644, exclusive create | 아래 계정2개만 정의. 기존 계정 repurpose 금지 |
| /usr/local/lib/cyberpilot-native-e-lab | root:root 0755, components no-symlink | 검토된 고정 ELF만, E/W/caller 쓰기 불가 |
| 같은 경로의 e-bootstrap / fixed-worker | root:root 0555, filecap/setuid 없음 | 새 source/build SHA가 준비돼야 함. 기존 research binary 복사 금지 |
| /etc/cyberpilot-native-e-lab | root:root 0755 | root-owned fixed manifest 0444; E가 읽어야 하는 비밀 아닌 UID/hash만 |
| /etc/systemd/system/cyberpilot-native-e-lab.service | root:root 0644, exclusive create | 신규 unit만. drop-in/enable/자동 재시작 없음 |
| P와 .supervisor/D | PID1의 신규 P; D는 E UID, 기본0700 | 실제 delegate 파일/ancestor 권한/ACL/alias를 별도 검증 |
| private synthetic fixture | 새 cohort 전용 E 보유 scope | 기존 home/HOST/차량 데이터 없음. W에 directory FD 전달 없음 |

sysusers 제안 바이트(실제 .conf 파일은 만들지 않음):

~~~text
u cp-e-lab - "CyberPilot research E" /nonexistent /usr/sbin/nologin
u cp-w-lab - "CyberPilot research W" /nonexistent /usr/sbin/nologin
~~~

관리자는 같은 이름/UID의 기존 사용·group membership·local-only identity source를 확인해야 한다.
계정 생성은 passwd/group/shadow/gshadow 등 인증 DB를 바꿀 수 있다.
그 DB나 비밀번호 hash를 이 연구 로그/보고서에 복사하지 않는다. 계정 재활용은 금지한다.

## 5. systemd255 unit 제안 — 설치 불가 초안

이 블록은 검토용이며 unit 파일로 저장/verify/load/start하지 않았다.
ExecStart 대상은 현재 존재하는 배포 artifact가 아니다. 새 factory adapter도 아직 없다.

~~~ini
[Unit]
Description=CyberPilot fixed native E research cohort

[Service]
Type=exec
User=cp-e-lab
Group=cp-e-lab
ExecStart=/usr/local/lib/cyberpilot-native-e-lab/e-bootstrap
WorkingDirectory=/
UMask=0077
Delegate=cpu memory pids
DelegateSubgroup=.supervisor
CapabilityBoundingSet=CAP_SETUID CAP_SETGID
AmbientCapabilities=CAP_SETUID CAP_SETGID
NoNewPrivileges=yes
PrivateUsers=no
ProtectControlGroups=no
RestrictNamespaces=yes
RestrictAddressFamilies=AF_UNIX
SystemCallArchitectures=native
LimitCORE=0
RuntimeMaxSec=30s
TimeoutStartSec=5s
TimeoutStopSec=5s
MemoryMax=128M
MemorySwapMax=0
TasksMax=8
CPUQuota=25%
KillMode=control-group
SendSIGKILL=yes
Restart=no
StandardInput=null
StandardOutput=null
StandardError=null
~~~

[Install]/ExecStartPre/Post/ExecStop/Environment/EnvironmentFile/credentials/socket activation은 추가하지 않는다.
E 결과는 F가 처음부터 보유한 전용 연결로 제한한다. 연결 생성/상속을 담당할 factory adapter는 미구현이다.
위 unit만으로 연결이나 original grant가 만들어지지 않는다. null stdio를 성공 receipt로 삼지 않는다.
**IPC/unit 통합 설계 자체도 미완**이다. 현재 블록은 resource/credential 요구사항 초안일 뿐 최종 unit bytes가 아니다.
P0에서 systemd255가 지원하는 private FD/manager handoff 방식을 하나 선정하고, 정확한 unit 변경,
원본 연결 생성·상속·닫기·EOF·수신FD 수/type·오류 정리까지 별도 검토해야 한다.
단순히 adapter binary를 구현했다고 이 unit이 ready가 되지 않는다. 미확인 D-Bus FD property는 제안하지 않는다.
따라서 후보 footprint도 미확정이며 socket/helper/추가 파일이 필요하면 변경 manifest와 승인을 갱신해야 한다.

F adapter는 신규 job을 만드는 최초 live 연결과 신규 P 생성을 연결하고, P 생성 전에
외부 writer를 배제하며 cohort1개만 허용해야 한다. 고정 unit명이나 InvocationID 문자열만으로는 부족하다.
살아 있는 원래 factory context가 없는 기존 unit attach/재start는 거부한다.
PID1이 만든 P와 .control/.supervisor의 실제 owner/limits/빈 inner node를 확인하고,
service-created P와 E-created D 주장을 구분한다. DelegateSubgroup이 적용되지 않으면 중단한다.
controller 활성화의 ancestor/sibling 영향도 미래 관리자 review 대상이다.

상한은 작은 합성 lab용이며 H 안전 기준이 아니다. 실제 kernel 값과 capability/NNP를 readback하고,
unsupported/unknown이면 worker0으로 끝낸다. unit start만으로 검증됐다고 하지 않는다.
RuntimeMaxSec은 active runtime 상한이며 시작/종료까지 포함한 정확한30초가 아니다.
Type=exec, TimeoutStartSec=5s, TimeoutStopSec=5s의 별도 phase와 계측 오차를 기록한다.
기존 서비스나 WSL 전체의 restart/shutdown은 필요하지 않으며 이번에도 하지 않았다.

## 6. 현 코드와의 호환성 및 필수 변경

| base source | 현재 동작 | 새 backend의 필수 작업 |
| --- | --- | --- |
| domain_supervisor.c L40–71/L219–238 | fd0 AF_UNIX protocol, 현재 membership을 P로 취급 | null stdin은 호환 불가. .supervisor를 P로 오인하지 말고 original F endpoint와 원본 P grant를 별도 전달·검증. parent 경로 추정만으로 authority 획득 금지 |
| L126–149/L176–179 | child /proc/fd/exe 검사 | UID 분리 뒤 읽기 제한 가능. SYS_PTRACE 추가나 실패의 PASS 처리 없이 새 원본 exec/entry 증명 설계·검증 |
| L153–170 | domain_supervisor/domain_worker 이름, worker owner==geteuid 검사 | 새 root-owned 보호 code는 현재 검사를 통과하지 않음. 원본 executable FD와 보호 설치 증거를 검증하는 별도 backend 필요 |
| L183–194 | 고정 exec/FD seal/PDEATHSIG | W credential/cap/NNP/인자 filter seal. UID/GID 변경 뒤 PDEATHSIG 재설정·원본 parent 관계 재확인 |
| L265 | E가 직접 clone3 child 생성 | original child/pidfd/wait 유지. F가 생성한 PID를 받는 것으로 대체 금지 |
| L285/L306 | D kill, pidfd fallback | 다른 UID에 pidfd signal은 EPERM 가능. CAP_KILL 추가 없음. 새 backend의 원본 D/fence 기반 한 번 stop으로 명시 |
| lab.py/domain.py | user-manager gate, caller-writable build/sidecar | 새 보호 code/manager-factory backend 필요. 기존 path를 그대로 privileged 실행하지 않음 |

pidfd는 target identity를 안정시키지만 signal permission을 면제하지 않는다.
원본 child wait와 signal은 다른 권한 문제다. cross-UID exec/FD entry 증명은 현재 미설계·미구현이다.
고정 보호 image를 trusted child prelude에서 execveat하고 원본 연결로 phase를 묶는 방향은 가능하지만,
자기신고 JSON이나 문자열 hash만으로 기존 /proc guard를 대체해서는 안 된다.
PR_SET_PDEATHSIG는 credential 변화에 의해 지워질 수 있으므로 credential seal 이후 다시 설정하고
아직 원본 parent가 살아 있는지 확인해야 한다. parent-death signal도 native D cleanup 증거는 아니다.

D birth 전에 pids controller와 D pids.max=1을 설정/readback하고 W에는 write 권한을 주지 않는 안이다.
E는 D 밖이므로 D의1task 상한에 포함되지 않는다. 이 상한만으로 membership/custody를 증명하지 않으며,
밖으로 move하는 행위는 별도 권한 거부로 검증해야 한다.

D authority가 불확실하면 group kill/remove 금지다. 별UID pidfd fallback 불가는 실패/잔류이지 성공이 아니다.
다른 handle/PID/path로 복구하거나 UNKNOWN을 F에 전달해 같은 D 연산을 재시도하지 않는다.
독립적인 PID1 외부 timeout은 신규 P에 대한 TCB 안전 상한이며 native cleanup 성공과 별도로 기록한다.
외부 timeout만 기대하고 original E의 안전 조건이 미충족인 채 W를 시작하지 않는다.

## 7. 미래 관리자 트랜잭션 — 이번 전부 NOT_RUN

먼저 새 bootstrap/F adapter와 고정 worker를 무권한 환경에서 구현·테스트·review한다.
정확한 source/build hash, account ID, unit bytes, 보호 경로를 채운 변경 manifest와
별도 관리자 변경 승인이 갖춰질 때까지 아래 명령은 실행하지 않는다.
자동 적용 script, sudoers/polkit 허용, 일반 remote launcher는 이번 제안에 없다.

| 순서 | 전제/미래 작업 | 영향 | 확인·중단 조건 |
| --- | --- | --- | --- |
| P0 | source/build/ABI/protocol/credential seal/factory fresh-P 증명 검증 | 연구 workspace만 | artifact SHA/IPC 통합 미확정이면 OS 변경0 |
| P1 | 지정 account2/path/unit명 충돌·ACL·local UID·필요 controller만 제한 확인 | read-only | 기존 것을 채택하지 않고 STOP |
| P2 | 관리자가 지정 sysusers 제안을 exclusive create하고 systemd-sysusers /etc/sysusers.d/cyberpilot-native-e-lab.conf | 인증DB와 새 UID/GID2쌍 | nologin/home 없음/부가group 없음/숫자 비중복. private DB 수집 금지 |
| P3 | 지정 새 directory를 비재귀 생성, 검증된 artifact/manifest를 exclusive install | 지정 보호 경로만 | O_EXCL/O_NOFOLLOW 상당, component/owner/mode/SHA/ACL. overwrite0 |
| P4 | 신규 unit만 exclusive create, systemd-analyze verify /etc/systemd/system/cyberpilot-native-e-lab.service | 새 unitfile | verify는 문법 진단이며 F1 증명/start 권한이 아님 |
| P5 | 관리자가 systemctl daemon-reload | system manager 설정 재독 | 기존 service 재시작은 없지만 전역 reload 영향이 있어 별도 승인 필요 |
| P6 | original F context에서 고정 신규 cohort1개만 생성 | 새 P와 E, gate 실패면 W0 | 기존 unit attach/start-by-name API 금지. 단순 systemctl start로 대체 금지 |
| P7 | 실제 limits/caps/UID/code/cgroup, positive control을 갖춘 거부 test | 승인된 새 synthetic actor만 | ADR T01–T15 및 아래 Q gate 전부. mock과 실제 OS 분리 |
| P8 | E 원본 handle로 한 번 stop/wait/remove, F retirement 검증 | 이번 신규 cohort만 | UNKNOWN이면 quarantine, 다음 기동/UID reuse 금지 |

P3에서 install -m의 overwrite 기본 동작을 검증 없이 사용하지 않는다.
미구현 artifact에 대해 copy 명령이나 hash를 만들어내지 않는다. 현재 P0가 충족되지 않아 P2 이후 실행 불가다.
공개 broker/socket, wheel/sudo group, setcap, setuid bit, timer/enable은 추가하지 않는다.

## 8. Rollback과 quarantine

완전한 PRE 복원과 안전 정지는 다르다. 새 system UID를 삭제하면 재할당 위험이 있으므로,
일반 rollback은 **entry를 닫고 이번 소유분의 unit/code만 조건부로 회수·보전**하는 것이다.
인증DB의 과거 copy 복원이나 account 삭제는 포함하지 않는다. 예약 account가 남는 사실을 보고한다.

| 상태 | 미래에 허용할 rollback | 금지 |
| --- | --- | --- |
| P0/P1만 수행 | 연구 제안을 폐기 가능 | OS를 변경했다고 보고 |
| account 생성·미start | 새2UID/GID를 nologin으로 예약 유지. 이번 exclusive-created config의 동일성 확인 후만 별도 회수 기록 | userdel/groupdel, 자동UID 재사용, 인증DB 전체 restore |
| code/unit 생성·미start | 이번 생성 hash/원본 inode가 확실한 신규 unit/code만 회수. 관리자 reload 필요 | 기존 path 삭제, rm -rf, 다른 사람 변경 overwrite, 추측 enable/disable |
| original live cohort·authority 확정 | original E가 stop/reap. 고정 F context만 retirement 관찰 | 이름/PID/receipt 재attach, 다른 unit/user-manager stop |
| kill/wait/close/unlink/fence UNKNOWN | admission 닫힘 유지, UID/GID/artifact 예약·quarantine, 미확인 잔류 보고 | native 성공 승격, 재시도, 불명확한 대상 수동 정리 |
| native retire 확정 | 이번 파일의 소유 증거 대조 후 필요하면 신규 unit만 회수·관리자 reload | 과거 cohort 재사용. 다음 실행은 별도 검토한 fresh generation |

F adapter의 live context가 사라지면 이름 기반 stop으로 전환하지 않는다.
PID1의 기존 상한 처리는 원래 신규 unit에만 작용하며 역사 UNKNOWN을 해소하지 않는다.
P가 사라져도 UID 재활용 안전, 외부 alias 또는 async 처리 소멸은 증명되지 않는다.
WSL shutdown/terminate, logout, 기존 process 살해는 rollback 방법이 아니다.

## 9. 미래 acceptance / no-go

[ADR-F1 T01–T15](ADMISSION_FENCE_CUSTODY_ADR.md)를 유지하며 다음을 추가한다. 전부 이번 미실행.

| ID | 검증 대상 | no-go |
| --- | --- | --- |
| Q01 | F/E/W credential, 실제 namespace, original cohort binding | UID 숫자나 unit명만 |
| Q02 | seal 뒤 E/W P/E/I/A=0, NNP=1, saved/fs ID, group0 | CapEff만0, CapBnd0의 허위 주장 |
| Q03 | UID0/타UID/GID/다른 ABI 경유 전환을 filter로 거부 | syscall 이름만의 filter, 미승인 host에서 권한획득 test |
| Q04 | P original birth, E-created D, E 밖, clone3 born-D | F-created D, 기존 unit 채택 |
| Q05 | 다른UID /proc 제한·signal EPERM 유지, 동등 이상 새 entry proof | SYS_PTRACE/KILL 추가, 기존 guard 약화, JSON 자기신고 대체 |
| Q06 | caller/W의 code/control/SCM/proc alias 변경 거부와 actor positive control | 불법 path 사전거부만으로 OS proof |
| Q07 | 실제 kernel 상한, 단일 cohort, 직접child wait, D stop1회 | 상한 미적용, 중복 시도, 모호한 성공 |
| Q08 | F 소실/expiry/outer teardown 뒤 admission 닫힘과 identity 예약 | 과거 기록 recovery, 옛UNKNOWN 해소, account 재할당 |
| Q09 | credential 전환 이후 PDEATHSIG와 원본 parent 관계 | 설정이 전환 뒤 유지된다는 가정, parent-death를 cleanup 성공으로 간주 |
| Q10 | factory endpoint/원본 P FD/실제 .supervisor 관계, FD count/type/EOF 거부, unit 통합 | null stdin으로 현binary 실행, membership dirname을 authority로 간주, 임의 endpoint/FD 공개 API |

초기 capability2는 고권한 TCB 증가다. filter/entry proof/factory가 미구현인 현재는
OS provisioning ready=NO, fenced lab ready=NO, runtime qualification=NO다.

## 10. 이번 상태와 다음 구현 단위

이번 실시: source/primary docs 읽기, 새 계획·보고·evidence, append-only 진척, 로컬 commit/bundle만.
미실시: account/permission/unit/cgroup/service/설정/의존 변경, build/test/lab/worker, push/PR/upload.
provider_registration=UNBOUND. 옛16 evidence available0/UNAVAILABLE. 모든14 flag는 false 유지.

다음 작업은 **무권한 연구 branch에서 고정 credential-seal bootstrap의 순수 TDD 구현**이다.
필요한 syscall 경계/실패 주입은 test에 두며, 실제 UID 전환/cap 부여/system unit은 실행하지 않는다.
이것이 끝나도 F fresh-P/entry proof가 미완이면 P0를 충족하지 않아 OS 변경은 시작하지 않는다.

## 11. 일차 근거와 설계 구분

다음은 API 근거이며 이 노트PC에서의 적용·권한 증명이 아니다.
위임/DelegateSubgroup: [systemd v255 resource-control](https://raw.githubusercontent.com/systemd/systemd/v255/man/systemd.resource-control.xml).
cap/NNP와 syscall 이름 filter: [systemd v255 exec](https://raw.githubusercontent.com/systemd/systemd/v255/man/systemd.exec.xml).
cap 의미/bounding 조건: [capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html).
UID 전환: [setresuid(2)](https://man7.org/linux/man-pages/man2/setresuid.2.html).
직접 birth: [clone(2)](https://man7.org/linux/man-pages/man2/clone.2.html).
다른UID /proc 조건: [proc_pid_exe(5)](https://man7.org/linux/man-pages/man5/proc_pid_exe.5.html).
signal 권한: [pidfd_send_signal(2)](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html).
직접child wait: [wait(2)](https://man7.org/linux/man-pages/man2/waitid.2.html).
parent-death credential 영향: [PR_SET_PDEATHSIG](https://man7.org/linux/man-pages/man2/PR_SET_PDEATHSIG.2const.html).
account 형식: [sysusers.d v255](https://raw.githubusercontent.com/systemd/systemd/v255/man/sysusers.d.xml).
외부 timeout/stop: [systemd service v255](https://raw.githubusercontent.com/systemd/systemd/v255/man/systemd.service.xml),
[systemd kill v255](https://raw.githubusercontent.com/systemd/systemd/v255/man/systemd.kill.xml).
이동 제약: [kernel cgroup-v2](https://docs.kernel.org/admin-guide/cgroup-v2.html).
역할·권한 phase·정지 규칙은 그 근거로 선택한 연구 제안이며 이미 구현한 기능이 아니다.
