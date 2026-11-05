# Provisioning plan 독립 검토 기록

Result: PASS_DOCUMENT_CONSISTENCY_ONLY  
Reviewer: 독립 provisioning_plan_review agent  
Base: aadf62ff3d826ed432b412f18143d5fa1144d4ba  
최종 검토 plan SHA256: 27cf1e2de8159ef70fd6446a464dedb2e95881504c45f6cad90436e82b48644b  
검토 input evidence SHA256: 03cbfa542a3144bd16de21e3aa66922e5cb0bc2559d5d6f2b6442adbe16300c1

범위: 계획/evidence와 기존 ADR-F1, domain_supervisor.c, lab.py, domain.py, fixed-worker source 대조.
보호된41파일 일치를 확인했다. reviewer는 edit/network/build/test/lab/OS/account/service/cgroup 작업을 하지 않았다.

초기 지적과 반영:
1. fd0 AF_UNIX와 P membership 검사를 unit의 null stdin/.supervisor에 그대로 적용할 수 없다.
   §6에 원본 endpoint/P grant 필요와 현binary 비호환을 추가하고 Q10으로 검증 조건을 고정했다.
2. IPC/unit 통합이 binary 부재보다 앞선 미완 설계라는 점을 명시해야 한다.
   §5에서 정확한 private transport/FD 수명/unit footprint가 P0에서 별도 확정돼야 함을 명시했다.
3. 작성자 source 대조에서 root-owned worker의 owner/name guard 비호환과
   credential 변경 후 PDEATHSIG 재설정 필요를 추가했다. 최종 reviewer가 함께 확인했다.

수정된 최종 plan에서 남은 중대한 모순은 없었다. 검토 후 plan bytes 변경 없음.
적용은 NOT_APPLY_READY다. fresh-P factory/handoff, 인자 제한 bootstrap/seal,
cross-UID exec-entry 증명, 정확한 unit/보호 artifact/host 정책/별도 관리자 승인이 남아 있다.
E-created direct child/D, W saved/fs IDs/groups seal, 옛자원 attach 금지,
manager outer cleanup 분리, UID reuse 없는 quarantine은 상위 ADR와 일치한다.

이후 최종 evidence에 status/review metadata만 작성자가 추가했다. 원래 검토 input은 제한된 로그에 보존했다.
최종 보고서/PLAN/PROGRESS/인계 manifest는 author self-review·문서 검증 범위다.
독립 runtime/OS 검증이나 새 코드 전체의 C0/I0 인증을 주장하지 않는다.
UNBOUND, qualification available0/16 UNAVAILABLE, 14flags false 유지.
