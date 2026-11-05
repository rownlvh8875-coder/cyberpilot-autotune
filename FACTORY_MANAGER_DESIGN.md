# Native factory private-manager fixture

Base4595279c63052c5d24a43916600fb423cdc1e674.
Scope: ADMIN_CHANGE_TRANSACTION A01–A05의 native component/fixture 구현.
Actual system-manager backend, protected host factory, P/D grant, credentials, W는 미연결이다.

## 파일/API

- research/factory_manager/factory.c: fm_run_fixed(void), 고정 request/lifecycle.
- request.c: 내부 typed StartTransientUnit encoder. profile는 data이며 적용하지 않는다.
- sdbus_abi.h: systemd v255 공개 ABI의 최소 선언. 기존 libsystemd.so.0 사용, 설치 없음.
- internal.h: constructor가 만든 원본 link의 내부 표현, 외부 adoption API 아님.
- unbound.c: 기본 transport는 ENOSYS. actual bus/address 연결 경로 없음.
- tests/native/factory_fake_manager.c: 실제 private sd-bus server + 고정 E probe만.
- tests/native/factory_manager_driver.c: 실패 주입, production code의 env/CLI switch 없음.

기본 binary는 UNAVAILABLE/E0/Start0이다.
native fixture만 별도 test constructor를 link한다. fm_run_fixed는 같은 process에서 한 번만 시도한다.
메모리 one-shot은 persistent intent/F1 승인이나 원본 resource custody를 대신하지 않는다.

## 실제 topology

F가 새 private bus socketpair와 M child를 clone3하고 original M pidfd를 보유한다.
synthetic M이 private endpoint를 실제 D-Bus h로 받아 duplicate하고 message FD를 release한다.
M이 E child를 clone3하고 original E pidfd로 wait한다. F는 E PID/pidfd를 받거나 채택하지 않는다.
E는 컴파일된 작은 protocol probe이고 actual E exec/privilege/cgroup/W를 구현한 것이 아니다.

F와 M은 기존 libsystemd로 EXTERNAL 인증·Hello·bus-client·UNIX FD negotiation,
GetNameOwner→AddMatch2개→Subscribe→StartTransientUnit→JobRemoved→UnrefUnit을 교환한다.
실제 system bus, filesystem/public listener, systemd unit/service 생성은 없다.
M은 request의 ExecStart path를 실행하지 않는다. UID/caps/limits도 적용하지 않는다.

F가 만든 두 번째 socketpair의 E endpoint 하나가 실제 SCM_RIGHTS로 M에 전달된다.
M은 message borrowed FD를 duplicate한 뒤 message unref가 borrowed ref를 닫았는지 확인한다.
M은 E가 종료해도 자기 duplicate를 유지하며 E의 명시적 shutdown/EOF가 필요하다.
E가 shutdown 없이 단순 close/exit하면 F가 protocol PASS로 처리하지 않는다.

## lifecycle

F callback은 JobRemoved/NameOwnerChanged 데이터를 복사·검사할 뿐 resource 작업을 하지 않는다.
실행 단계에서 reply job/unit/generation/owner와 단일 event를 대조한다.
nonce unit은 F가 생성한다. modefail/AddRef/고정 type·단위/profile와 단일 h property를 검사한다.
이 wire request는 administrator payload나 검증된 host manifest가 아니다.

Start attempt는 call 전에 소비한다. 취소·timeout·error 뒤 재송신/이름 attach는 없다.
F/M 각자의 원래 child wait는 시도 전에 handle을 소비한다.
마지막 Unref 응답 전후 event를 버리지 않도록 PRIVATE M의 원래 exit를 wait한 뒤
private bus의 마지막 queue/disconnect까지 관찰한다.
이 private-peer EOF 규칙은 실제 shared system bus에 그대로 이식할 수 없다.

D-Bus ID/owner는 이 새 private fake-manager 세대의 correlation이다.
PID1 권한/physical host identity로 승격하지 않는다. 실제 manager owner/generation binding은 아직 없다.
문자열/PID/FD 번호/receipt를 가져와 기존 resource를 얻는 외부 API는 없다.

## 정리 결과의 한계

소유한 native FD close 결과와 original M/E wait는 확인한다.
sd_bus_close_unref/unref 등 library의 내부 close는 void/pointer API여서 개별 syscall 결과를 관측하지 못한다.
따라서 normal report도 cleanup=NATIVE_HANDLES_CONFIRMED_LIBRARY_UNAVAILABLE,
library_close_result=UNAVAILABLE이다. 전체 HOST cleanup 성공을 선언하지 않는다.
outcome PRIVATE_MANAGER_PROTOCOL_COMPLETE는 protocol 관측만 뜻한다.
native error/unknown은 UNKNOWN, 재시도/복구 없음. bus FD reuse면 foreign number를 닫지 않는다.

SDK가 disconnect 때 자기 FD를 소비하면 그 번호를 다시 close하지 않는다.
library object를 안전하게 해제할 수 없는 mapping loss는 process-bound residue로 남는다.
고정 fixture native process 종료 후의 kernel FD table release와 library close syscall 성공은 다른 사실이다.
일반 daemon·외부 writer/async drain·arbitrary descendant containment는 검증하지 않는다.

## 검증/비목표

real kernel: 새 same-UID M/E, private fd passing, original parent wait, explicit shutdown, no E PID adoption.
real library: typed D-Bus wire/UNIX FD marshalling, client readiness and signals.
synthetic: manager method semantics, job/ref lifecycle, E body, proposed resource/credential profile.
NOT_RUN: actual system bus/PID1, unit/account/permission/cgroup/credential changes, W/vehicle/H.

계약서18pins와 역사 source는 수정하지 않는다.
UNBOUND,16UNAVAILABLE/available0,14flagsfalse 유지. 보호 코드/실제 UID/loader/F1/P/D gate 미충족.

## 최종 보완/범위
Constructor는 native fd/anchor를 먼저 추적하고 set_fd 성공 뒤만 library owner로 표기한다.
new/set_fd 실패의 own-FD-count regression2건, changed bus-ID/sender mutation을 포함해46PASS.
request encoder는 A01-A05용 subset이며 actual manager에 적용 가능한 전체 unit/hardening payload가 아니다.
private owner:1.0/job1 correlation을 shared system bus의 동적 owner/job identity로 일반화하지 않는다.
