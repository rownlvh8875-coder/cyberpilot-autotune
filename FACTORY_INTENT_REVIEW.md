# Factory intent — 독립 source review와 author 수정
Date:2026-11-06. Base:d24cb17ef9e557286f8555680a033518529d10a4.
범위: new native intent/coordinator/header/default constructor, test driver/Python tests,
설계/PLAN/PROGRESS 및 관련 old manager/handoff. OS/build/test를 reviewer가 실행하지 않았다.

Verdict:REQUEST_CHANGES. Critical0 / Important1 / material Minor0.

## Important1 — 마지막 anchor의 inode-only close
release()는 fd/anchor의 OFD를 검증하고 primary를 close한 뒤 남은 anchor를
inode/type만 대조해 close했다. primary close가 success를 반환하더라도 hook이
anchor를 같은 inode의 다른 OFD로 교체하면 foreign FD가 닫혔다.
기존 close_fd_reuse는 primary 번호만 교체해 이 경우를 놓쳤다.

Author RED:
test_final_anchor_replacement_is_never_closed_by_inode_only_check의
leaf_anchor_reuse/root_anchor_reuse 모두 foreign_fd_open=false로 실패.
Repair:
primary만 소비/close하고 마지막 anchor 슬롯을 terminal static process context에 남긴다.
다시 사용·닫기·경로/receipt 기반 복구를 하지 않는다.
native_release=PARTIAL_REFS_RETAINED. 전체 cleanup 성공이 아니며 bounded residue를 택했다.
55 focused GREEN. 전체 최종 회귀 결과는 LOCAL_FACTORY_INTENT_REPORT.md에 기록.

## 별도 test instrumentation 문제
UBSan first51PASS/2FAIL: compiler fortification이 __pread_chk를 사용해 test-only pread hook을 우회했다.
nm 및 설치된 unistd-decl.h로 확인하고 fortified 함수도 실제 checked 함수를 유지한 채 wrap했다.
fortification/UBSan 기준을 낮추지 않았다. production 수정을 위한 실패가 아니었다.
그 hook 추가와 최종 repair는 author 검증이며 독립 post-fix review/C0/I0는 주장하지 않는다.

## Reviewer가 인증하지 않은 범위
power-loss durability, 악성 sameUID writer 배제, protected F1/crossUID custody,
actual system manager, unit/cgroup execution, qualification evidence.
판정: 이번 latch 범위 밖이며 모두 UNAVAILABLE/NOT_RUN 또는 미구현으로 유지한다.
기존 관리자 B01–B10을 해제하지 않는다. 재리뷰 대신 RED→GREEN와 full regression을 수행한다.

## 추가 author 계약·lab 경계 점검
uninspected/unknown durability=false를 RED6으로 재현하고 null로 바꿨다(새5 cases).
pause fault fixture의 자체 deadline 부재를 RED로 재현한 뒤 고정 alarm4를 추가했다(새1 case).
새 직접 자식 원래 Popen만 정지·wait했고 기존 process/service를 제어하지 않았다.
최종61 focused/UBSan/GCOV PASS는 author 검증이며 독립 post-fix review가 아니다.
