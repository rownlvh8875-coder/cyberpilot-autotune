# LOCAL NATIVE FACTORY / MANAGER FIXTURE REPORT

STATUS: PASS_NATIVE_PRIVATE_PROTOCOL_WITH_LIMITATIONS
Base: 4595279c63052c5d24a43916600fb423cdc1e674
Branch: research/native-e-factory-manager
Date: 2026-11-05

## 구현 결과

[설계/API](FACTORY_MANAGER_DESIGN.md)에 따라 native private-manager component를 구현했다.
새 코드가 실제 libsystemd를 이용해 D-Bus 메시지와 UNIX FD를 주고받는다.
manager 역할은 새 private synthetic M process다. 실제 system manager/PID1이 아니다.

| 파일 | 기능 |
| --- | --- |
| [factory.c](research/factory_manager/factory.c) | fm_run_fixed(void), callback 관측/실행 단계 분리, 단일 요청, 원본 M wait/최종 event drain |
| [request.c](research/factory_manager/request.c) | typed StartTransientUnit-shaped request, modefail/AddRef/limits/caps/data와 실제 h FD |
| [internal.h](research/factory_manager/internal.h) | 내부 constructor의 owned link·FD 이전 여부, 외부 adoption API 없음 |
| [sdbus_abi.h](research/factory_manager/sdbus_abi.h) | 공개 ABI 최소 선언. 기존 runtime SONAME만 사용 |
| [unbound.c](research/factory_manager/unbound.c) | default transport ENOSYS. actual bus 연결/대체 없음 |
| [synthetic manager](tests/native/factory_fake_manager.c) | 실제 private server·M-owned E birth/pidfd/wait·보관 FD와 shutdown 검사 |
| [실패 주입](tests/native/factory_manager_driver.c) | test-only wire/library/native boundary fault |
| [regression](tests/test_factory_manager.py) | native/lifetime/error/FD ownership·one-shot46cases |

개발 header/pkg-config/linker dev symlink는 없고 libsystemd.so.0만 존재했다.
시스템 패키지는 설치하지 않았다. v255 공개 ABI 선언으로 기존 라이브러리에 직접 link했다.
이는 loader closure·배포판 binary 진위 또는 protected code origin 인증이 아니다.
새 component는 제품/provider/wheel에 통합하지 않았다.

## 실제로 검증한 관계

F가 새 socketpair와 M을 직접 생성하고 원래 M pidfd를 갖는다.
M은 D-Bus message의 E endpoint를 h/SCM_RIGHTS로 받고 duplicate한다.
message unref 뒤 borrowed FD가 닫혔고 retained duplicate가 같은 OFD인지 확인한다.
M이 고정 E probe를 직접 생성하고 원래 E pidfd로 wait한다.
F는 E PID/pidfd를 전달받아 control/wait authority로 채택하지 않는다.
E는 actual E service/exec backend가 아닌, 작은 컴파일된 protocol probe다.

실제 라이브러리 경로는 EXTERNAL/Hello→bus-client·FD negotiation→GetNameOwner→
AddMatch2개→Subscribe→StartTransientUnit→JobRemoved→UnrefUnit이다.
owner:1.0/job1/private bus ID는 이 고정 fixture의 correlation이다.
실제 shared system bus에서의 동적 manager/job identity 처리는 아직 구현하지 않았다.

M이 E endpoint duplicate를 계속 보유하므로 E의 단순 close/exit는 F에 EOF를 만들지 못한다.
명시적 E shutdown/EOF를 확인해야 protocol PASS다.
단순 종료·추가 bytes·잘못된 nonce/FD/property/signature·event owner/generation/job 오류를 거부했다.
callback은 관측만 기록한다. 마지막 Unref 전후 이벤트는 원래 PRIVATE M exit 뒤 queue까지 확인한다.
이 private peer disconnect 규칙을 실제 shared system bus 종료 조건으로 이식할 수 없다.

request의 User/caps/NNP/자원 상한/ExecStart는 **전부 wire data**다.
M은 그 path를 실행하거나 계정·권한·limits를 적용하지 않는다.
현재 encoder는 A01–A05 검증용 subset이고 완전한 관리자 unit/hardening payload가 아니다.
P/D/F1 grant가 없어 W는 시작하지 않는다. 실제 H/payload/차량 데이터도 없다.

## 범위별 결과

| 항목 | 결과와 한계 |
| --- | --- |
| A01 | default UNAVAILABLE/Start0/E0, bus-client·UNIXFD 미지원 거부. 실제 host discovery/authorization 없음 |
| A02 | subscribe 전 관측 setup, owner/job/unit/ID/late·duplicate 이벤트 거부. 실제 PID1 provenance 미검증 |
| A03 | call 전에 attempt 소비, cancel/timeout/clone-return 불확실성 뒤 원본 handle 정리·재요청0 |
| A04 | 실제 D-Bus h 전달·duplicate/borrow lifetime·명시 shutdown. 모든 negative FD leak 부재까지 증명하지 않음 |
| A05 | 실제 F→M 및 M→E parent/original wait. F가 E를 직접 만든 것으로 표현하지 않음 |
| 실제 manager/unit/cgroup/credential/P/D/W | NOT_RUN / 미연결 |
| protected factory/code/loader·crossUID | UNAVAILABLE / 미구현 |
| provider/qualification | UNBOUND /16UNAVAILABLE, available0 |

## 정리 결과를 성공으로 과장하지 않음

원본 native handles의 close와 각 부모의 단일 child wait는 관측한다.
sd_bus_close_unref/unref의 내부 close syscall 결과는 void/pointer API가 노출하지 않는다.
따라서 normal output도 아래처럼 분리한다.

~~~json
{
  "outcome": "PRIVATE_MANAGER_PROTOCOL_COMPLETE",
  "cleanup": "NATIVE_HANDLES_CONFIRMED_LIBRARY_UNAVAILABLE",
  "library_close_result": "UNAVAILABLE",
  "actual_manager": false,
  "actual_unit_created": false,
  "worker_started": false
}
~~~

SDK 내부 close 결과를 확인했다거나 전체 HOST cleanup이 성공했다고 주장하지 않는다.
안전하게 library object를 해제할 수 없는 FD mapping loss는 process-bound UNKNOWN residue로 남긴다.
foreign numeric FD는 다시 닫지 않는다. context/receipt/숫자로 복구하지 않는다.
SDK 자동 disconnect가 소비한 FD 번호도 native code가 다시 close하지 않는다.
원본 wait handle은 시도 전에 소비해 오류 뒤 cleanup path에서 wait를 반복하지 않는다.
고정 native process 종료와 kernel FD table 회수는 library syscall 성공과 별도 사실이다.
일반 daemon·arbitrary descendants·외부 writer/async drain은 검증 범위 밖이다.

## 최종 테스트와 계측

| 검사 | 결과 |
| --- | --- |
| 신규 tests | **46 PASS /0FAIL/0SKIP** |
| 전체 연구 tests | **448 PASS /0FAIL/0SKIP** = 기존402 + 신규46 |
| UBSan | 동일46case PASS. 동적 libsystemd 자체는 계측 제외 |
| GCOV fixture 실행 | 동일46case PASS. child dump는 test-only exit shim |
| factory.c | lines97.12%(135/139), branch outcomes66.29%(175/264) |
| request.c | lines100%(41/41), branch outcomes51%(51/100) |
| unbound.c | line100%(1/1), branches 없음 |
| synthetic M test code | lines99.43%, branch outcomes67.09%, 제품 코드 계측과 구분 |
| 기존 연구 Python coverage | 91.74%, 기준90 유지. 신규 C/SDK와 별도 |
| Ruff/format | exit0,55files formatted |
| mypy | 기존 Python10modules exit0. 신규 C는 strict compiler 검증 |
| native compiler | GCC -std=c11 -O2 -Wall -Wextra -Werror PASS |
| 신규 package build | NOT_RUN, packaging 변경 없음 |
| 이전 제품2786PASS | 이번 NOT_RERUN, fresh 합계에 넣지 않음 |
| 기존80파일 | SHA25680/80, ledgers append-only |

46은448에 포함된다. UBSan·GCOV·반복·개발 RED 결과를 PASS 합계에 더하지 않았다.
native C branch outcome이 모두 covered인 것은 아니다.
SDK 내부·kernel/systemd·OS permission coverage로 해석하지 않는다.

독립 리뷰 Important1(부분 constructor FD leak)은 실제 own-FD count RED2로 재현했다.
SDK new 전 실패와 set_fd 전 실패를 나눠 원래 socket/anchor와 library ownership 이전을 추적하도록 수정했다.
Minor generation comparison test gap은 두 번째 ID 변경 case로 보완했다.
[리뷰 기록](FACTORY_MANAGER_REVIEW.md)에 initial reviewed hashes와 수정 범위가 있다.
수정 뒤 final-tree 독립 재리뷰/C0/I0 인증은 선언하지 않는다.

그 외 개발 RED: 잘못된 unit prefix 길이, Unref 주변 late event3건,
library close 정보 누락, 동일 process 두 번째 attempt.
test-only compiler 경고/import 정렬도 수정했다.
모두 별도 logs에 남기고 최종 전체448/UBSan46/GCOV46과 정적 검증을 다시 확인했다.
새 deps 설치·sudo/root·global 환경/권한 설정 변경은 하지 않았다.

## 환경과 재실행

Ubuntu-24.04 WSL2 noninteractive, Linux x86_64, 기존 GCC/runtime/venv.
관측 kernel은6.18.33.2-microsoft-standard-WSL2, 실행 EUID1000이다.
호출 사이의 namespace·세대 연속성을 가정하지 않고 fixture별 새 private process/socket을 만든다.
actual system/user bus를 열거나 address/listener를 설정하는 경로는 없다.

~~~text
.venv/bin/python -m pytest -q tests/test_factory_manager.py --basetemp=<new-private-path>
.venv/bin/python -m pytest -q --cov=native_e_lab --cov-branch --cov-fail-under=90 --basetemp=<another-new-path>
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src/native_e_lab research/admin_review/check_bundle.py
~~~

테스트는 새 tmp/build/log만 사용한다. 기존 evidence basetemp를 재사용하지 않는다.
UBSan/GCOV runner와 GCOV child exit helper는 private 전달 logs에 있다.
핵심 C뿐 아니라 OS SDK 파일/기존 package/config은 수정하지 않았다.
새 연구 branch local commit/bundle만 만든다. push/merge/PR/upload 없음.
최종 SHA/CLEAN/hash는 별도 FINAL_DELIVERY.json에 있다.

## 상태와 다음 작업 하나

provider_registration=UNBOUND. 필수16종 모두 UNAVAILABLE/available0.
9개 admission/qualification flag와 나머지 actual_payload_released,cleanup_allowed,
recovery_execution_authorized,H_executed,HREQ004_qualified를 포함한14개 전부 false 유지.
이번 허용된 고정 합성 child 실행/신규 lab 자원 정리는 제품 payload/cleanup 권한과 구분한다.
실제 관리자 적용 readiness=NO다.

**다음은 기존 P→E 원본 handoff와 W entry를 M-owned E 경로에 결합하는 무권한 통합 fixture 구현이다.**
기존 component를 재사용하고 실제 UID/cgroup/F1 적용은 계속 별도 gate로 둔다.
현재 code는 그 통합·보호된 system-bus factory를 대체하지 않는다.

[공개 sd-bus ABI v255](https://github.com/systemd/systemd/blob/v255/src/systemd/sd-bus.h),
[private socketpair server 예제](https://github.com/systemd/systemd/blob/v255/src/libsystemd/sd-bus/test-bus-server.c),
[내부 FD release 구현 참고](https://github.com/systemd/systemd/blob/v255/src/libsystemd/sd-bus/sd-bus.c#L125)는
API 근거다. 이 노트북의 package 진위/host qualification을 증명하지 않는다.
