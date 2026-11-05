# Parent handoff 독립 코드 리뷰 / 수정 검증

Base: a961f2ce2d3a50b5989ec75902352f5954f94ad4
Independent verdict: REQUEST_CHANGES (Critical0 / Important2 / Minor1)
Final verification: AUTHOR_FIX_AND_FULL_REGRESSION / NO_SECOND_INDEPENDENT_REVIEW

읽은 source의 SHA256:
- handoff.c: 8736059f9590725fa29f2e829ce122c99c46c003d91e375c9c3870f7f1c77db4
- parent_handoff_driver.c: 98acf40fa58a0e47c201a164b66849107063214683fbc6369d3c9aae3f74e961
- test_parent_handoff.py: 156476f932db56b102c156e8811c969fa3e992a9090b9f484ca386f392c54d9c

## 지적과 조치

1. Important: cgroup v2만 거부하고 v1은 mkdirat에 도달할 수 있었다.
   fstatfs 경계 fixture RED1/positive2로 재현했다. linux/magic.h의 두 magic을 생성 전에 거부한다.
   실제 cgroup을 만들거나 쓰지 않았다.
2. Important: P 제거 뒤 마지막 base FD close가 UNKNOWN이면 parent_removed=true가 가능하다.
   구현은 이미 그 사실을 출력했지만 전체 실패에 P가 남는다는 설명은 부정확했다.
   late-close 표적 test로 기존 동작을 확인하고, contract를 전제거 불확실/후제거 불확실로 분리했다.
   후자의 제거 사실을 유지하며 UNKNOWN으로 실패한다. P를 재생성하거나 rollback/retry하지 않는다.
3. Minor를 강화: 기존 수신-FD 카운터는 두 번째 close를 무시했다.
   double-close probe가 잘못 PASS하는 RED를 재현한 뒤, test-only 원본 OFD anchor와
   수신 generation별 close-attempt 계산으로 중복을 잡는다. probe의 peer98/전체REJECTED를 확인했다.
   추적용 anchor는 test 소유이며 확인 뒤 닫는다. payload/worker FD seal의 증거가 아니다.

한 번의 수정 pass 뒤 focused33PASS, 연구269PASS/제품2786PASS.
수정 중 test-only prototype 선언 순서 오류로 compile 실패33개가 있었고 선언 수정 후 strict compiler 통과했다.
후속 독립 재리뷰는 하지 않아 수정 뒤 C0/I0를 주장하지 않는다. 최종 source hash는 evidence에 있다.
Reviewer는 파일 조회 외에 tests/build/native 실행/network/OS 변경을 하지 않았다.

## 제외 범위에 대한 작성자 판단

- protected factory/systemd IPC와 cross-UID authority: 이번 regular fixture로 증명할 수 없어 미검증 유지.
- 실제 cgroup provisioning/custody: 현재 양쪽 cgroup filesystem을 거부하며 해당 작업을 하지 않는다.
- W/RUN/exec/FD entry: W를 생성하지 않았다. 다음 고정 통합 단계의 별도 조건이다.
- 적대적 FD-table race, mkdir/open/unlink의 atomic provenance와 동권한 namespace writer 배제:
  trusted single-owner lab의 검사만으로 보장하지 않는다. ADR-F1이 요구한 OS boundary는 계속 미충족이다.
- 장치/USB/차량 검증: 수행하지 않았으며 이 결과를 전이하지 않는다.

Rulings:
- 기존 FD-rejecting worker protocol을 보존하고 새 NPG1 parent channel을 분리했다.
  비용은 별도 native framing의 감사 부담이며, worker에 parent FD를 허용하는 예외는 만들지 않았다.
- 후제거 close UNKNOWN은 제거 사실과 정리 불확실성을 함께 보존한다. 잘못 적용하면 가짜 rollback/회수 성공이 된다.
- 새 residue/진단 로그는 보존한다. 비용은 소량의 private 임시 디렉터리/로그 보관이다.
보류한 minor: 없음. UNBOUND/16UNAVAILABLE/14false 유지.
