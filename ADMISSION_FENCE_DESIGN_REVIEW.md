# Admission fence / custody 독립 설계 리뷰

Result: NO_MATERIAL_FINDINGS  
Mode: READ_ONLY / DESIGN_ONLY  
Reviewer: 별도 admission_design_review agent  
Source base: 694604e0722373d6666600e202e454b79a9d3d02  
ADR SHA256: 5d8fd6c4a8c17ff3d8a51f56376558f990655eb29633c09f4bb72ddc83ce8573

검토 범위는 ADMISSION_FENCE_CUSTODY_ADR.md와 base의 domain_supervisor.c, domain.py,
lab.py다. reviewer는 세 source가 base와 동일함을 확인했다. 본 리뷰 기록/최종 보고서/JSON은
작성자의 정리 및 문서 검증 범위다. runtime이나 새 구현 전체에 대한 독립 C0/I0 인증이 아니다.

- §2: X의 위협은 실제 OS mutation authority에 조건부이며, 같은 UID의 보편 권한을 단정하지 않는다.
- §3: mkdir/open, membership snapshot/kill, name check/unlink 공백을 source와 대조했다.
- §6–7: systemd/factory가 만든 외부 P와 E가 직접 만드는 D를 구분한다.
  원본 live handoff, 기존 alias 배제, 보호된 code origin이 현재 path/hash보다 강한 미구현 요구임을 명시했다.
- §6/§8: broker 종료/expiry 후에도 배제를 유지하며, 불확실 kill/wait/close/unlink를
  다른 alias로 재시도하지 않는 규약과 quarantine을 명시했다.
- §9: mock 회귀와 실제 OS 배제·custody 증거를 분리했다.

중대한 지적과 수정 요구: 없음. 따라서 검토 후 ADR bytes 수정 없음.
리뷰는 tests/build/lab/service/cgroup/network/kernel 정책 검증을 수행하지 않았다.
F1은 PROPOSED/미구현. 이전 trusted-single-owner PASS와 b2f2d50 UNKNOWN은 그대로다.
UNBOUND, 기존16 evidence UNAVAILABLE, 모든14 flags false를 유지한다.
