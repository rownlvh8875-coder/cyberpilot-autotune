# Native factory intent successor — 제한된 영속 중복 차단
Date:2026-11-06. Base:d24cb17ef9e557286f8555680a033518529d10a4.
Status:RESEARCH_COMPONENT / HOST_APPLY_BLOCKED.

## 결정
기존 ADR-A2의 attempt.intent를 실제 native filesystem 거래로 구현하고,
기존 fm_run_fixed의 private synthetic manager 앞에 연결한다.
이전 real-cgroup lab을 반복하지 않는다. 실제 system bus/새 unit/cgroup/권한 작업은 없다.

외부 API는 fi_run_fixed(void)뿐이다. caller path/FD/PID/unit/command/receipt를 받지 않는다.
기본 scope constructor는 ENOSYS: root0/intent0/Start0/E0.
별도 test constructor만 새 private fixture의 고정 state directory를 원본 FD+OFD anchor로 연다.
기존 parser/request/fixed E probe를 재사용하며 manager는 계속 synthetic이다.

## 순서와 실패 의미
in-memory one-shot 소비 → 고정 constructor → 원본 parent/root OFD·name·owner/mode 검사
→ 64-byte 새 nonce/monotonic record 준비 → attempt.intent O_CREAT|O_EXCL|O_NOFOLLOW
→ 원본 file anchor → 단일 bounded write/readback → file fsync → root fsync
→ 원본/name/content 재검사 → 기존 고정 manager 단일 요청 → 재검사 → 원본 FD release.
partial/EINTR/close/clock/fsync/ownership 결과 불명확은 UNKNOWN/DENY, 같은 작업 재시도 없음.
intent는 성공/실패/조기종료 뒤에도 남는다. 삭제/reset/recovery/adopt API가 없다.
기존 intent 내용은 읽거나 해석하지 않는다. 빈/손상/위조/과거 성공 receipt도 모두 DENY.
file/root fsync는 관측된 syscall 성공일 뿐 power loss/하드웨어 durability 인증이 아니다.
닫기 전에 원본 OFD를 확인하고 close 시도 전에 숫자 소유권을 소비한다.
anchor 미확보 또는 다른 OFD로 번호 재사용되면 foreign FD를 닫지 않고 UNKNOWN/residue를 남긴다.

## F1 / cross-UID 적용 계약
이 latch는 중복 생성 억제 일부다. same-UID fixture를 전체 F1 admission fence라 부르지 않는다.
보호된 관리자 factory는 root-protected code/loader/state 원본, 외부 actor denial,
실제 동적 bus owner/job/InvocationID/P creation binding, E/W 실제 UID/credential seal,
E가 만든 D에 born-in-D, 원본 wait/stop/drain을 별도로 구현·검증해야 한다.
관리자가 만든 P와 E-created D는 구분한다. E는 D 바깥이다.
현재 모듈은 P custody/readonly mount/namespace/external-writer drain을 구현하지 않는다.
새 계정/권한/서비스/설치를 수행하거나 qualification evidence를 작성하지 않는다.
B01–B10과 과거16 evidence는 이 latch PASS로 해제되지 않는다.

## 검증
단일 승자/동시2factory/새 process 재실행/crash-after-create 및 after-durable,
기존 모든 종류 intent·name replacement·same-inode 다른 OFD·socket FD reuse,
partial write/unknown write/fsync/close/clock/random·부분constructor·manager실패,
원본기록 tamper·한 process 두번째 요청·영수증 재생 모두 negative.
새 fixture만 사용하며 생성물/불확실성 로그는 보존한다.
native source는 old123 non-ledger files와 분리한다. PLAN/PROGRESS는 append-only.
UNBOUND,16UNAVAILABLE,14false, no push/admin/vehicle 유지.

## 리뷰 후 원본 FD release의 제한
close(primary) 후 comparator가 없어 마지막 anchor를 inode만으로 닫는 결함을 RED2로 재현했다.
수정: pair 검증 뒤 primary만 소비/close한다. 마지막 anchor 슬롯은 다시 사용/close하지 않는다.
terminal intent는 static process-bound 상태에 남고, 새 호출은 one-shot에서 차단된다.
native_release=PARTIAL_REFS_RETAINED는 전체 정리 성공이 아니다. 의도한 bounded FD residue다.
unknown close는 계속 UNKNOWN이다. process exit의 자동 FD 회수는 별개이며 SDK close/drain 증명은 없다.

관측값 규칙: open/write/fsync 불확실성 또는 조사하지 않은 기존 marker의 durability는 JSON null이다.
두 번째 one-shot 요청은 과거 live 상태를 복원하지 않아 durability=null이다.
false는 이 attempt가 새 intent 생성 자체를 수행하지 않았다고 확인되는 경우만 사용한다.

테스트 pause child는 고정 alarm4로 스스로 종료한다. harness 유실 시에도 무한 대기하지 않는다.
