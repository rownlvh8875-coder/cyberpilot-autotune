# ADR-A2 — 현재 F/E/W용 관리자 변경 검토안

**Status: PROPOSED / REVIEW_ONLY / APPLY_BLOCKED**
Date: 2026-11-05
Deciders: 향후 별도 관리자 변경 승인 주체. 이번 구현자는 설계 선택과 검증만 담당한다.
Base: 8c0058ee8b24e7acd1de8bec248563d623ff60e4
상위 [F1 계약](ADMISSION_FENCE_CUSTODY_ADR.md), 보존된 [이전 provisioning 계획](NATIVE_E_PROVISIONING_PLAN.md).

## 1. 결정과 달라진 점

**고정 native F adapter가 local system bus의 StartTransientUnit을 한 번 호출하고,
새 E service의 fd0에 직접 private socket endpoint를 전달하는 방향**을 선택한다.
고정 no-arg adapter와 PID1을 합쳐 F TCB로 정의한다. 새 root daemon이나 공개 socket은 두지 않는다.
기존 user-manager, 로그인 세션, 전역 sudoers/polkit, WSL 설정을 바꾸지 않는다.
미래 lab의 Linux/WSL namespace와 host-principal scope를 명시해야 한다.
namespace-relative / 또는 namespace UID0을 Windows/물리 host root로 해석하지 않는다.

이는 미래 구현 방향이다. 이번에는 DBus 호출, unit 생성/verify/load/start, 계정 생성,
privilege/credential/cgroup 변경을 수행하지 않았다.
같은 이름의 기존 자원이 있으면 채택하지 않는다. 현재 연구 binary를 service에 설치하지 않는다.

이전 계획의 영구 /etc/systemd/system service + daemon-reload 안을 이번 대안에서는 사용하지 않는다.
runtime transient service와 관리자 설치 파일은 별개다.
이 문서가 이전 제안을 자동 채택·수정하거나 실제 정책을 바꾼 것은 아니다.

## 2. 선택지

| 안 | 이점 | 비용/판정 |
| --- | --- | --- |
| 영구 service + 별도 filesystem listener | 익숙한 설정 | 추가 listener/인증/수명, reload 필요. 이번 안에서 제외 |
| F가 직접 E fork 후 cgroup으로 이동 | 원래 E pidfd 직접 보유 | service-manager lifecycle/정확한 born-in-D와 별개이고 move race 발생. 제외 |
| system bus transient unit + private stdin FD | 공개 listener·영구 unit·reload 최소화 | manager FD 수명과 새 host backend 필요. **선택한 검토안** |
| 기존 research binary를 root/caps로 그대로 실행 | 새 구현 적음 | root/CGfs 거부·고정 synthetic UID·caller-owned code·regular P. 호환 불가 |

## 3. 확인한 API와 미확인 부분

systemd **v255 source**에서 StandardInputFileDescriptor를 D-Bus type h로 받고
F_DUPFD_CLOEXEC로 복사하는 경로를 확인했다.
이는 .service 파일의 숫자 FD directive가 아니다. fd0 자체를 숫자 JSON으로 지정하지 않는다.
[dbus-service.c v255](https://github.com/systemd/systemd/blob/v255/src/core/dbus-service.c#L439)

v255 systemd-run의 direct stdio 경로와 AddRef=true 사용을 확인했다.
AddRef는 bus-client 연결일 때 사용하므로 local system bus client를 선택하고
manager private socket 직접 연결로 자동 대체하지 않는다.
AddRef는 manager object 참조이며 kernel FD 또는 실행 권한의 대체물이 아니다.
[run.c v255](https://github.com/systemd/systemd/blob/v255/src/run/run.c#L624)

런타임에서 이 노트북의 PID1·bus/정책·FD negotiation이 해당 경로를 허용하는지는 **미검증**이다.
Ubuntu minor 패치 동등성도 이 문서로 인증하지 않는다.
호환되지 않으면 worker0으로 차단한다. shell/systemd-run/start-by-name fallback은 없다.
이번에는 패키지 설치·API 탐색을 위한 bus 연결·관리자 prompt를 실행하지 않았다.

DelegateSubgroup=.supervisor는 E를 P의 child subgroup에 두는 요구다.
P는 PID1-created이고 내부 D는 E가 직접 만들며 E는 D 밖에 있어야 한다.
cpu/memory/pids 위임은 ancestor/sibling controller 활성화 영향을 가질 수 있어
“새 unit 외 아무 변화 없음”이라고 가정하지 않는다.
[resource-control v255](https://github.com/systemd/systemd/blob/v255/man/systemd.resource-control.xml#L1235)

[request-contract.json](research/admin_review/request-contract.json)은 검토용 필드·type·단위 설명이다.
완전한 D-Bus payload도, materialize 가능한 launch manifest도 아니다.
Exec artifact와 live stdin endpoint는 UNAVAILABLE다.
30s→RuntimeMaxUSec30000000, 128MiB→MemoryMax134217728,
CPU25%→CPUQuotaPerSecUSec250000 등의 대응만 고정한다.
[bus-unit-util.c v255](https://github.com/systemd/systemd/blob/v255/src/shared/bus-unit-util.c#L620)

## 4. 미래 live 생성·FD 순서 — 미구현

1. 관리자가 별도로 승인한 root-owned fixed-factory만 no-arg로 실행한다.
   일반 사용자 실행은 privilege 획득 없이 거부한다. setuid/filecap·새 polkit rule은 없다.
2. 보호된 code/loader/manifest, 새 local principal2개, 이전 잔류·cohort 부재를 검증한다.
   승인 문서/receipt/hash로 기존 살아 있는 자원을 다시 얻지 않는다.
3. root private /var/lib/cyberpilot-native-e-lab/attempt.intent를 O_EXCL/no-follow로 만들고 파일·부모를 fsync한다.
   존재·불확실성은 DENY다. 이 기록은 authority를 만들거나 cleanup을 복구하지 않는다.
4. F가 새 AF_UNIX stream socketpair를 만들고 OFD anchors를 보유한다.
   E endpoint 하나만 message의 UNIX FD로 전달한다. F endpoint는 manager/W에 전달하지 않는다.
5. 같은 live bus 연결에서 job signal 구독→factory-generated nonce service명→
   StartTransientUnit(mode=fail, AddRef=true, aux=[])를 한 번 호출한다.
   임의 unit명/command/path/PID/FD를 받는 API는 없다. 실패·불명확 응답 뒤 재요청하지 않는다.
6. PID1이 새 P와 .supervisor/E를 만든다. E는 private protocol의 승인된 grant까지 W를 생성하지 않는다.
   F가 live creation job/object, 신규 namespace-visible P, E entry와 정책을 결합해야 한다.
   **현재 이 결합은 없다.** unit명/InvocationID/controlgroup 문자열만으로 original P를 주장하지 않는다.
7. 신뢰된 생성 구간에 원래 P FD를 확보하고 E-only grant를 보낸다.
   E는 P/D fence·limit·code/UID/NNP/capability·외부 actor 거부 증거가 모두 유효할 때만
   D mkdir→원본 refs→CLONE_INTO_CGROUP|CLONE_PIDFD W birth를 한 번 수행한다.
8. E는 W의 실제 credential seal과 fixed exec/FD/parent 관계를 검증한다.
   P는 F가 공급하지만 D는 E-created다. F가 만든 D를 전달해 이름만 바꾸지 않는다.
9. E는 D 원본 권한으로 stop1회, 직접 W pidfd wait1회, drain과 제거를 확인한다.
   E의 일반 pidfd signal이 다른 UID에도 허용된다고 가정하지 않는다.
10. E는 명시적 write-half shutdown/EOF를 포함한 최종 protocol을 완료한다.
    F는 native 종료 사실과 manager retirement/독립 timeout을 구분해 기록한다.
    manager reference는 원래 live 연결에서만 release한다. 이전 이름으로 다시 붙지 않는다.

PID1은 전달받은 E endpoint의 duplicate를 유지할 수 있다.
따라서 E process exit/한 FD close만으로 F가 EOF를 받는다고 가정하면 안 된다.
E의 명시적 shutdown(SHUT_WR)은 공유 socket의 write-half에 작용하므로 그 순서를 검증해야 한다.
이 descriptor 잔존은 FD 전달의 실제 OS acceptance case다. 이번에 실험하지 않았다.

## 5. F의 E 소유권과 E의 W 소유권 구분

현재 harness는 F가 E를 clone3하고 F가 원래 E pidfd를 wait한다.
새 service 안에서는 **PID1이 E의 부모**다. adapter는 E의 parent가 아니다.
MainPID를 읽어 pidfd_open(E)한 것을 original birth handle이라고 부르지 않는다.
adapter의 waitid(E)는 직접 자식 wait를 대체하지 못한다.
선택한 F는 manager+adapter의 합성 TCB이며 manager의 생성/종료 책임과
adapter의 private 연결을 별도 provenance로 검증해야 한다. 이 구현은 아직 없다.

E가 W를 직접 생성하고 원래 W pidfd로 wait하는 요구는 유지한다.
worker의 self exe/FD witness는 보호된 fixed trampoline/code origin과 함께 해석한다.
같은 UID fixture의 self-report를 악성 E에 대한 독립 attestation으로 승격하지 않는다.

## 6. 현재 코드와의 차이

현재 frozen source18개는 [source-pins.json](research/admin_review/source-pins.json)에 있다.
이것은 연구 base의 byte identity이며 관리자 승인·배포 binary manifest가 아니다.

| source / 위치 | 현재 사실 | host backend 전제 |
| --- | --- | --- |
| integration.c:15 | IDs17001/17002/18001/18002는 synthetic 상수 | 실제 local allocator 결과와 보호 manifest·filter 일치. 현재 값 재사용 금지 |
| integration.c:33–35 | image owner==geteuid, caller-private build dir | root-owned no-write code/loader 원본 FD 검증. 검사를 지우고 root code 채택하지 않음 |
| integration.c:164–170 | W는 CLONE_PIDFD만, 일반 child | E-created D에서 CLONE_INTO_CGROUP birth, E outside D 검증 |
| integration.c:252–256 | root·cgroup filesystem 거부 | 현재 main 사용 금지. 별도 F와 E backend 필요 |
| integration.c:268–274 | F→E 직접 clone | PID1 생성 E의 별도 private FD/manager lifecycle binding |
| entry_credential.c + seal.c | logic/순서 구현, syscall shim 검증 | 실제 cross-UID/caps/NNP/filter/PDEATHSIG readback과 거부 test |
| handoff.c:reap_original | pidfd SIGKILL fallback | W UID 분리 후 EPERM 유지, CAP_KILL 추가 없이 원본 D stop |
| domain_supervisor.c | 별도 기존 internal-D prototype | credential/entry/private grant와 미결합. 과거 PASS 이식 금지 |
| protocol/handles | nonce/seq/FD reuse consistency | OS-exclusive F1 집행을 대신하지 않음 |

## 7. 보호 경로와 변화 footprint

[change-manifest.json](research/admin_review/change-manifest.json)은 **검토용**이다.
실제 경로/계정 존재 여부는 이번에 조회·생성하지 않았다.
모든 신규 경로는 component no-symlink/owner/mode/ACL/별도 mount alias 검증을 미래 gate로 둔다.
설치 전 신규 path가 이미 존재하면 채택·overwrite하지 않고 중단한다.
F launch 때 code/config/state parent는 이번에 검증한 보호 설치분이어야 한다.
attempt.intent leaf가 이미 존재하면 성공 기록이어도 무조건 DENY한다.
기존 /etc, /usr/local/lib, /var/lib 등 parent는 적합성을 확인하며 임의 생성/재귀 변경하지 않는다.
별도 /run private directory나 filesystem socket은 이 안에 필요하지 않다.

| 미래 대상 | owner/mode | 변화·제한 |
| --- | --- | --- |
| cp-e-lab/cp-w-lab | 새 local static UID/GID, nologin, no home | 숫자 UNAVAILABLE. 로그인/NSS/추가 group·UID 재활용 금지 |
| /etc/sysusers.d/cyberpilot-native-e-lab.conf | root:root0644 | 계정2개 제안, exclusive create. 인증DB를 로그로 수집하지 않음 |
| /usr/local/lib/cyberpilot-native-e-lab | root:root0755 | 새 보호 code store, 이미 존재하면 중단 |
| fixed-factory/e-bootstrap/fixed-worker | root:root0555 | source/build/ABI/hash·loader closure UNAVAILABLE, 현재 research binary 금지 |
| /etc/cyberpilot-native-e-lab/manifest.json | root:root0444, parent0755 | 비밀 아닌 고정 ID·artifact 명세. 데이터만으로 live authority 복구 불가 |
| /var/lib/cyberpilot-native-e-lab + attempt.intent | root:root0700 +0600 | directory는 설치 때, leaf는 F가 P 생성 전에 O_EXCL·fsync. UNKNOWN/재부팅 뒤 자동 해제 없음 |
| /run/systemd/transient/…nonce.service | PID1 관리 | StartTransientUnit가 만드는 신규 transient record. 파일을 직접 삭제·수정하지 않음 |
| 신규 P/.supervisor/D | manager/E 역할별 권한 | P는 manager-created, D는 E-created. W mutation 거부를 실제로 검증 |

**계정 도구의 기존 전역 파일 영향도 있다.**
v255 systemd-sysusers는 인증 DB 갱신 외에 /etc/passwd-, /etc/group-, /etc/shadow-, /etc/gshadow-를
새 backup으로 교체할 수 있고, 사용 가능한 nscd의 passwd/group cache를 invalidation할 수 있다.
새 path 목록만으로 이 작업의 전체 footprint를 표현할 수 없다.
[sysusers.c v255](https://github.com/systemd/systemd/blob/v255/src/sysusers/sysusers.c#L265)
이 backup overwrite/cache 영향은 현재 승인되지 않았다. 내용·password hash는 수집하지 않는다.
배포판별 lock/temp/NSS 부작용은 UNAVAILABLE이며 별도 local source/도구 검토가 필요하다.
manifest의 account_tool_effects와 B10에 이 전역 영향을 포함한다. 실제 P2 실행은 계속 차단한다.

영구 service/drop-in/timer/socket, enable/linger, daemon-reload는 선택한 안에 필요하지 않다.
반면 계정·code·root private intent와 controller 영향은 실제 관리자 변경이다.
기존 서비스 재시작/WSL 재부팅/새 네트워크 공개는 이 안의 절차가 아니다.
UID/GID 예약과 one-shot 기록이 남는다는 비용을 수용한다.

## 8. 미충족 hard gates

[거래·rollback 절차](ADMIN_CHANGE_TRANSACTION.md)를 참고한다.
B01–B10은 전부 **현재 차단**이며 삭제·true 기입으로 해제할 수 없다.
최소 host backend와 실제 source/build artifacts가 없는 지금은 계정 설치조차 시작하지 않는다.
API source 문서 확인, unit INI parse, no-forward shim, content checker PASS는 OS acceptance가 아니다.

## 9. 검토 도구의 의미

[check_bundle.py](research/admin_review/check_bundle.py)는 고정 연구 파일만 읽어
추가 directives, privilege 확대, source drift, placeholder의 허위 build 승격 등을 탐지한다.
shell/DBus/socket/container/설치/실행·정리 API가 없다.
PASS일 때도 apply=BLOCKED, host_commands=NOT_IMPLEMENTED를 출력한다.
검토용 config는 printable ASCII와 TAB/LF/CR만 허용해 ConfigParser의 Unicode/기타 control
공백 정규화가 systemd와 다르게 보안 directive를 숨기지 못하게 한다.
[systemd v255 whitespace 정의](https://github.com/systemd/systemd/blob/v255/src/basic/string-util.h#L10)
완전한 systemd parser/loader 검증은 아니다.
trusted workspace용 내용 lint이며 서명된 provenance, 공격자 배제 또는 보안 경계가 아니다.
.source-pins와 checker를 함께 바꾸는 행위를 방어하는 외부 root of trust도 아니다.

~~~text
.venv/bin/python research/admin_review/check_bundle.py
.venv/bin/python -m pytest -q tests/test_admin_review.py --basetemp=<new-private-path>
~~~

## 10. 결과·다음 구현 단위

이 안은 관리자 **검토 묶음**으로 완성하지만 OS apply-ready는 아니다.
provider_registration=UNBOUND,16UNAVAILABLE/available0, 모든14flag=false를 유지한다.
기존 qualification 정책 채택·승인 레코드는 만들지 않는다.

- [ ] 다음 독립 구현: **보호된 factory의 private FD + manager lifecycle backend를 무권한 fixture로 구현**.
- [ ] 그 source/build/loader와 UID mapping이 준비된 뒤 별도 관리자 변경 검토/승인.
- [ ] 실제 OS denial/credential/born-in-D/정지·quarantine 검증은 그 이후 별도 lab.

현재 금지된 관리자 적용을 “다음단계 진행”만으로 실행하지 않는다.
연구 코드는 기존 최종 자격·실차 readiness와 분리한다.
