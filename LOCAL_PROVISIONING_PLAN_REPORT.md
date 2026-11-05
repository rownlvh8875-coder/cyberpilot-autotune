# LOCAL PROVISIONING PLAN REPORT

STATUS: PLAN_COMPLETE_WITH_IMPLEMENTATION_BLOCKERS  
OS provisioning: NOT_APPLY_READY  
Scope: PLAN_ONLY

## 결과

[F/E/W 최소 변경안](NATIVE_E_PROVISIONING_PLAN.md)을 작성하고 독립 문서 검토를 마쳤다.
F는 신뢰된 system manager/fixed factory adapter, E/W는 새 비로그인 static host 계정 두 개로 제안한다.
E 초기 bootstrap에만 SETUID/SETGID를 두고, worker 진입 전 credential/capability seal을 요구한다.
임의 UID 전환이 가능한 높은 권한임을 명시했으며 광범위 ptrace/kill/admin 권한은 추가하지 않는 안이다.

계정 생성만으로 실행 가능한 상태가 되지 않는다. 현재 source는 fd0 socket/P membership,
worker owner/name, child proc/FD inspection, pidfd signal fallback이 새 배치와 호환되지 않는다.
PDEATHSIG도 credential 전환 뒤 별도 재설정/검증이 필요하다.

가장 큰 미완은 original F endpoint/P grant를 전달하는 systemd255 IPC/unit 통합이다.
unit 블록은 최종 설치 artifact가 아니다. P0에서 정확한 private transport와 FD lifecycle/footprint를
확정·검토하기 전에는 현재 binary를 설치하거나 service를 시작할 수 없다.
이 작업은 그 blocker를 없앴다고 주장하지 않는다.

변경안은 필요한 경로/owner/mode, future 관리자 transaction/영향/검증,
rollback 및 UNKNOWN 시 계정/identity quarantine을 포함한다.
안전 rollback은 계정을 자동 삭제하거나 인증DB 전체를 과거 copy로 복원하는 방식이 아니다.
예약 account가 남을 수 있음을 구분했다. 과거 b2f2d50 UNKNOWN은 그대로 유지한다.

## 실제 실행과 변경

- 승인된 비대화형 Ubuntu-24.04 경로로 source/기존 보고서/PLAN/PROGRESS를 읽었다.
- base aadf62ff3d826ed432b412f18143d5fa1144d4ba와 CLEAN을 확인했다.
- 같은 isolated worktree에서 research/native-e-provisioning-plan 새 branch를 만들었다.
- 기존 tracked41파일의 SHA256을 동결했다. PLAN/PROGRESS는 append만 허용했다.
- 새 계획/보고서/review/evidence를 작성했다. account/path 존재 조회·UID 추정은 하지 않았다.
- 공개 primary systemd v255 source/man-pages/kernel 문서를 조회했다. 링크는 계획 §11에 있다.
  D-Bus FD property의 정확한 지원은 확정하지 않았고 존재하는 것처럼 설계에 넣지 않았다.
- 로컬 append-only commit과 별도 새 전달 폴더/bundle만 만든다. push/merge/PR/upload는 하지 않는다.

실제 명령(스크립트 본문은 제한된 파일 읽기/SHA256/문서 구조 검사):

~~~text
wsl.exe --distribution Ubuntu-24.04 --exec /usr/bin/python3 -I -B -
git branch --show-current
git rev-parse HEAD
git status --porcelain
git ls-files -z
git switch -c research/native-e-provisioning-plan
git diff --check
~~~

조회/branch 생성 exit0. 최종 commit은 전역/저장소 설정 변경 없이 command-local
Codex Research <codex-research@localhost> 작성자를 사용한다.
commit/bundle/verify의 실제 결과는 전달 폴더 logs/final-verification.json과 FINAL_DELIVERY.json에 기록한다.
새 unit이나 위 계획의 sysusers/verify/reload/start 명령은 실행하지 않았다.

## 검증 결과

| 항목 | 결과 | 범위 |
| --- | --- | --- |
| 기존 source/tests/config/옛 evidence/설계41파일 | 최종 SHA 대조 기록 참조 | 내용 보존 |
| PLAN/PROGRESS | append-only 검사 | 옛 내용 보존 |
| JSON14false/UNBOUND/0-of-16 | 구조 검사 | 승인·자격 부여 아님 |
| Q01–Q10/미래단계 P0–P8/로컬 문서 링크 | 구조 검사 | 실제 OS test 아님 |
| unit INI 필드 | Python parser로 문서 초안만 검사 | systemd syntax/semantic verify 아님 |
| runtime unit/제품 tests/lint/build/coverage | NOT_RUN_PLAN_ONLY | 코드·tests 변경 없음 |
| 새 user/unit/worker/cgroup | 0/0/0/0 | 실행 자격 관측 없음 |
| 이전178 harness/2786 product PASS | 역사 기록만 | 이번 PASS에 합산하지 않음 |

[독립 검토 기록](PROVISIONING_PLAN_REVIEW.md)에 수정 지적과 최종 plan SHA를 남겼다.
최종 plan 검토 결과는 PASS_DOCUMENT_CONSISTENCY_ONLY이며 적용/실행 가능성 PASS가 아니다.
보고서/evidence 최종 metadata와 전달 검사는 author self-review다.

## 권한 경계

설치/업데이트/sudo/관리자 승격/계정 생성/권한 설정/daemon-reload/
service 시작·재시작·정지/cgroup 쓰기/Docker/provider/payload/차량 실행을 하지 않았다.
WSL 비대화형 기동과 기존 서비스 자동 시작 가능성은 기존 승인 범위다.
별도 unit 생성이나 controller 변경을 하지 않았다.

모든14 flag는 false다. provider_registration=UNBOUND,
qualification required16/available0/UNAVAILABLE를 유지한다.
새 provisioning/lab/runtime 자격은 부여하지 않았다.

## 남은 일과 다음 작업 하나

fresh-P factory, private IPC/unit 통합, credential argument filter/seal,
cross-UID 원본 exec/FD proof, 보호 artifact와 별도 관리자 승인이 필요하다.
현재 계획은 적용 가능한 완제품이나 관리자 승인 요청이 아니다.

**다음 작업: 격리된 무권한 연구 branch에서 고정 credential-seal bootstrap을 순수 TDD로 구현한다.**
실제 UID 전환/cap 부여/system unit을 실행하지 않고 syscall 경계와 실패 semantics부터 검증할 수 있다.
이 구현만 통과해도 남은 F/IPC/entry proof를 충족하기 전에는 OS 변경을 시작하지 않는다.
