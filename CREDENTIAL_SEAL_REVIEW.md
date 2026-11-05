# Credential-seal 독립 코드 리뷰와 수정 검증

Base: f5c62ac0186e486f88d2cbb3e764e8da036e954a
Reviewer: 독립 credential_seal_review agent, read-only
Review verdict: REQUEST_CHANGES (Critical0 / Important2 / Minor1)
Final fix verification: AUTHOR_TDD_GREEN / NO_SECOND_INDEPENDENT_REVIEW

검토 파일과 당시 SHA256:
- seal.h: 3eb902431f4f3faf96c36a5b96bef4bd12ae77143ed9957f2ced413bc4d01f07
- seal.c: 0204e1e18460369c11f7473e43da872b47ce09b570c4cb31d4ef11ad9616c47b
- test_credential_seal.py: 597539ef8b1466509c732233bf862b475f05d792081e1fe9ed2d66c87c5c569c
- credential_seal_driver.c: cd1572934bc8c1c4af29e834bd212da1668bba334ec48fe6ad5a4cfa39b93065

## 지적과 한 번의 수정 pass

1. Important: __x86_64__는 x32의 __ILP32__도 허용한다. 필터는 x32 syscall을 kill하므로
   지원하지 않는 ABI가 빌드되는 결함이었다. 실제 guard를 compiler로 실행하는 test가 RED였고,
   ILP32/64-bit pointer/long 조건을 추가하여 GREEN을 확인했다. 다른 아키텍처 포팅은 하지 않았다.
2. Important: preflight close, post open/read/close, PR_GET_PDEATHSIG 오류 주입이 없었다.
   production error 경로는 존재했지만 의미 있는 회귀가 부족했다. phase별 fixture 오류를 추가해
   UNKNOWN, 한 번 close, 원상복구/재시도/추가 mutation 없음, 재호출 syscall0을 확인했다.
3. Minor를 필수 coverage로 재분류: 순차 replay만으로 동시 재진입 요구를 대체할 수 없다.
   syscall fixture 안에서 같은 attempt의 owner seal을 중첩 호출해 ALREADY_ATTEMPTED와
   nested syscall0/security write0을 확인했다. 별도 OS thread나 실제 credential 전환은 사용하지 않았다.

추가 test RED:7FAIL/1PASS; 수정 후 focused58PASS, 전체236PASS.
후속 독립 재리뷰를 하지 않았으므로 수정 뒤 전체 코드의 독립 C0/I0를 선언하지 않는다.
최종 source SHA는 evidence_credential_seal.json에 있다. 작성자가 전체 회귀·strict compiler·UBSan을 재검증했다.
Reviewer는 tests/build/native fixture/계정/service/cgroup/network를 실행하거나 파일을 수정하지 않았다.

## 리뷰가 승인하지 않은 범위와 작성자 판단

- 실제 kernel seccomp verifier/집행, 실제 UID/group/cap/prctl: 이번 금지 범위라 미실행.
  fixture 성공을 OS 성공으로 해석하면 잘못된 자격이 되므로 gate를 계속 닫는다.
- 원본 parent 생존/custody와 Q09 전체: PDEATHSIG 설정 조회만으로 충족되지 않는다. 미검증 유지.
- F fresh-P, original D, exec-entry/FD seal, payload/RUN, 통합·full syscall sandbox: 이번 component에 없음.
  합성 결과로 이를 보충하면 권한을 잘못 부여하므로 다음 구현/독립 gate로 남긴다.
- trusted proc provenance, 적대적 동시 credential/FD/mount 변경, process-wide lifetime: snapshot/메모리 attempt가
  보장하지 않는다. 실제 F1 host boundary 검증 전에는 보호된 live 실행이라고 부르지 않는다.
- OS/계정/service/cgroup/Docker/network/차량, provisioning/runtime qualification: 이번 미승인.
- reviewer는 부모가 보고한 수치/coverage를 직접 재실행하지 않았다. 최종 명령 로그가 근거다.

보류한 minor: 없음. evidence/진척 로그는 사용자 요구대로 보존하며 skill scratch cleanup은 실행하지 않는다.
그 비용은 소량의 로컬 진단 파일 보관이다. UNBOUND,16UNAVAILABLE,14false 유지.
