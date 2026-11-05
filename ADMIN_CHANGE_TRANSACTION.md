# 관리자 변경 거래·rollback 검토서 — 실행하지 않은 제안

STATUS: REVIEW_ONLY / ALL_OS_STEPS_NOT_RUN / APPLY_BLOCKED
기준: [ADR-A2](ADMIN_CHANGE_REVIEW.md), [변경 manifest](research/admin_review/change-manifest.json).
이 문서는 install script나 승인 레코드가 아니다. 아래 계정·파일·unit은 실제로 만들지 않았다.

## 1. 먼저 충족해야 하는10개 gate

| ID | 현재 차단 원인 | 적용 전에 필요한 실제 산출물·검증 |
| --- | --- | --- |
| B01 | protected fixed-factory 없음 | no-arg native backend, fresh job/object context, bus owner/connection 및 생성 중 취소 test |
| B02 | private FD/manager 경로 미실험 | local system bus FD negotiation, AddRef lifetime, duplicate endpoint/EOF/extraFD 거부, unsupported=worker0 |
| B03 | original P/F1 집행 미증명 | P 생성 전부터 retire까지 외부 name/membership/control/code/alias writer 권한 배제. ordinary actor positive control 포함 |
| B04 | privileged E backend 없음 | 일반 P/root/owner checks를 우회하지 않는 별도 host backend, protected origin, exact fixed API |
| B05 | 실제 UID/GID mapping 없음 | local 신규계정2개의 숫자·group/no-login/no-home 확인. synthetic17001 등을 추측 채택하지 않음 |
| B06 | build/loader artifacts 없음 | 고정 F/E/W source/build SHA·ABI·root-owned loader closure, no setuid/filecap, 환경·interpreter 제한 |
| B07 | cross-UID credential 실제 검증 없음 | UID/GID saved/fs/groups, P/E/I/A0, CapBnd의 정확한 잔여, NNP1, arg BPF/x32 우회 거부, PDEATHSIG/parent |
| B08 | 새 code와 internal D 미결합 | E-created D·pids.max1 readback, E outside, born-in-D W, D stop1회, original W wait1회, populated0 및 조건부 제거 |
| B09 | 외부 actor 거부 미증명 | 새 actor가 다른 허용 fixture에는 write 가능한 positive control, P/D/FD/proc/code/UID mutation은 OS에서 거부 |
| B10 | 실제 관리자 변경 승인 없음 | 위 exact 산출물·영향·상한·rollback을 검토한 별도 범위 승인. 기존14flag true로 대체하지 않음 |

이번 변경 검토 도구는 B01–B10을 해제할 수 없다.
재현하지 않은 cross-UID/manager/OS 효과는 UNAVAILABLE/NOT_RUN이다.
과거16 qualification 증거를 대체하거나 숫자를 늘리지 않는다.

## 2. 미래 관리자 단계와 영향

| 순서 | 미래 행위 | 영향/확인 | 실패하면 |
| --- | --- | --- | --- |
| P0 | 검토 source/build/loader/contract와 B01–B10 검증 | 현재 unresolved artifact/ID가 있으면 여기서 중단 | OS 변경0 |
| P1 | 지정 계정명/UID/GID/path/mount/ACL/기존 잔류만 제한 확인 | 기존 자원은 채택하지 않음; 인증DB 원문 수집 안 함 | 충돌 중단 |
| P2 | sysusers 제안 파일을 exclusive/no-follow 생성 후 관리자 실행 | auth DB와 기존 backup4개 교체 및 조건부 nscd cache 영향. 별도 승인 전 실행0 | 자동 DB restore/delete 없음 |
| P3 | 새 code/config/state parent만 비재귀 생성, artifact를 exclusive install | source/build/owner/mode/components/loader closure 검증, overwrite0 | 원래 이번 생성분만 증거에 따라 조건부 회수 |
| P4 | F가 /var/lib/cyberpilot-native-e-lab/attempt.intent를 exclusive 생성·fsync | intent는 재시도 억제만. 이미 존재/불확실하면 생성0 | quarantine, intent 재사용/삭제 금지 |
| P5 | 원래 F bus connection에서 transient service 한 번 생성 | Runtime30s/Start5s/Stop5s/128MiB/Swap0/Tasks8/CPU25% 및 caps/UID 실제 readback | worker gate 불충족이면 W0 |
| P6 | fixed E가 새 D를 만들고 원래 child를 직접 생성·관측 | controller enable의 ancestor/sibling 영향 승인 필요. 기존 unit 재시작 안 함 | 원래 handle로 한 번만 terminal 처리 |
| P7 | native stop/wait/drain/remove와 manager retirement를 구분 확인 | manager timeout은 독립 안전 상한이며 native 성공 증거가 아님 | UNKNOWN 보존·새 실행/UID 재사용 차단 |

P2의 전역 기존 파일 영향:
systemd-sysusers는 /etc/passwd,/etc/group,/etc/shadow,/etc/gshadow 및 각 trailing-dash backup을
변경·교체할 수 있다. nscd passwd/group cache invalidation도 가능하다.
이는 "새 계정2개/새 파일만"이라는 영향 범위를 넘는다.
기존 backup overwrite, 도구 lock/temp/NSS 부작용과 운영 복원 정책에 대한 별도 관리자 검토가
끝나지 않으면 실행하지 않는다. 실제 존재·내용·secrets는 이번에 조사하지 않았다.
[고정 v255 source](https://github.com/systemd/systemd/blob/v255/src/sysusers/sysusers.c#L866)

현재 P0 미충족이므로 P2 이후 실행 명령을 자동 생성하거나 호출하지 않는다.
미래에 사용될 구체적 계정 처리 명령은
systemd-sysusers /etc/sysusers.d/cyberpilot-native-e-lab.conf 이지만 이번에는 NOT_RUN이다.
확정되지 않은 artifact를 install/copy하는 placeholder 명령은 제공하지 않는다.
해당 원본 live factory backend가 없으므로 systemctl start나 systemd-run으로 대체하지 않는다.
선택한 transient 안에 daemon-reload/enable/linger는 없다.
관리자 명령을 실행하는 helper/sudo/승격 절차는 이번 code에 없다.

## 3. Principal·one-shot 상태

- E/W는 새 local static 계정이다. root/PID1은 TCB이며 coequal root 공격자 배제는 주장하지 않는다.
- 고정 F의 모든 새 실행은 동일한 root-protected /var/lib/cyberpilot-native-e-lab/attempt.intent의 exclusive 생성부터 시작한다.
  O_EXCL은 F들의 중복 생성 억제이고 P/D 외부 writer 전체를 배제하는 F1 fence가 아니다.
- intent는 파일·parent fsync까지 확인한다. 불명확한 생성도 DENY로 남긴다.
- intent 내용/해시/receipt는 existing unit/FD/PID/cgroup를 다시 얻는 키가 아니다.
- 한 번 소비한 intent는 성공 때도 자동 삭제·재arm하지 않는다.
  다음 cohort/principal 재사용은 별도 검토 대상이다.
- /run 상태가 재부팅으로 사라져도 /var/lib deny-only 기록과 계정 예약은 해제되지 않는다.
  reboot/host crash/WSL shutdown 실험은 이번 범위 밖이다.
- 기존 record를 overwrite/청소하거나 UID 재활용으로 막힘을 해소하지 않는다.

## 4. Rollback 결정표

| 실제 도달 상태 | 허용을 검토할 범위 | 계속 금지할 범위 |
| --- | --- | --- |
| 현재처럼 proposal만 작성 | OS rollback 불필요, 연구 branch/evidence 보존 | 적용했다고 보고 |
| 계정 생성, service 시작 전 | 신규 principal nologin/예약 유지, 이번 exclusive config/source 동일성 기록 | userdel/groupdel/UID 재할당/인증DB/기존 global backup 전체 자동 복원 |
| 새 code/config 설치, 시작 전 | 원래 이번 생성분의 inode/hash/live ownership 확인 후 조건부 파일 회수 | 기존 파일 overwrite, broad rm/chmod/chown |
| 원래 F/E live context 유지 | 원래 E가 D stop1회/W wait1회, 자기 scope closure·manager retirement 관찰 | numeric PID/unit명/receipt 재attach |
| F가 없어짐/결과 불명확/FD·wait·stop 오류 | admission 닫힘, intent/UID/artifact 예약·quarantine·잔류 보고 | 새 F가 예전 이름으로 stop/kill/remove, 재시도·성공 승격 |
| PID1 timeout으로 P 종료 관측 | 독립 외부 상한 사실만 기록 | native stop/drain/모든 alias retirement로 간주 |
| native/manager retirement 모두 확정 | 정확히 이번 소유분만 별도 관리자가 검토 | 다음 cohort 자동 생성, one-shot intent 자동 해제 |

원래 handle을 잃으면 다른 이름·PID·FD 숫자를 대체 권한으로 사용하지 않는다.
manager가 만든 /run/systemd/transient 파일을 수동으로 지워 unit을 정리하지 않는다.
기존 서비스·user-manager·WSL 전체를 stop/restart/terminate하는 것은 rollback이 아니다.
계정·intent가 남는 것은 완전 PRE 복원과 다르며 반드시 보고한다.

## 5. 새 backend의 오프라인 acceptance 목록

다음은 아직 실행하지 않은 구현 요구다. 이번 checker의 mutation tests와 혼동하지 않는다.

| ID | future test |
| --- | --- |
| A01 | exact no-arg factory, unsupported manager/system bus/FD feature면 create0 |
| A02 | subscriber setup→exclusive fail-mode start; duplicate/late job signal과 manager generation 변경 거부 |
| A03 | StartTransientUnit 반환 전 취소·불명확 응답에서 ownership/잔류 보존, 재요청0 |
| A04 | stdio UNIX FD 복제·PID1 endpoint 잔존과 explicit shutdown/EOF 순서, wrapper extraFD cleanup |
| A05 | PID1-created E를 adapter-created child/pidfd로 잘못 주장하지 않음 |
| A06 | protected root-owned image/loader manifest와 actual local UID/cap/filter 연결 |
| A07 | 원래 P live grant 없이는 D/W0, regular-P fixture를 host cgroup로 오인하지 않음 |
| A08 | E-created D, CLONE_INTO_CGROUP|CLONE_PIDFD, W no control/host directory FD |
| A09 | W UID 변경 뒤 /proc 제한·pidfd signal EPERM 유지, D 원본 stop만 허용 |
| A10 | sender/nonce/seq/generation/image/parent/FD/EOF/invalid metadata 실패가 성공으로 바뀌지 않음 |
| A11 | intent 재존재/소실/partial fsync/host reboot 후 authority 복구·UID reuse 없음 |
| A12 | stop/wait/close/remove 불확실성과 외부 timeout을 구분, 원본 handle 상실 시 quarantine |

scope-limited pure fixtures가 먼저이며 실제 OS 효과는 이후 별도 승인 lab에서만 확인한다.
외부 writer/async drain, readonly mount/namespace 및 실제 provider 자격은 여전히 미구현/미검증이다.

## 6. 정확한 다음 작업 하나

**A01–A05의 고정 factory private-FD/manager-lifecycle backend를 새 무권한 fixture로 구현한다.**
현재 노트북에서 관리자 권한 없이 개발 가능한 다음 code 단위다.
실제 bus start/unit/cgroup/UID 변경을 실행하는 구현과 혼합하지 않는다.
그 뒤에야 B01/B02의 source/build 검토 범위를 줄일 수 있다.
