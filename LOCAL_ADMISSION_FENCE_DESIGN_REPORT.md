# LOCAL ADMISSION FENCE / CUSTODY DESIGN REPORT

STATUS: DESIGN_COMPLETE  
Architecture: PROPOSED / DESIGN ONLY  
Strong-fence execution: BLOCKED_ENFORCEMENT_UNPROVEN

이번 작업은 native E의 다음 연구 단계인 admission fence와 원본 D custody 설계다.
구현·단위 테스트·OS 합성 실험을 추가하지 않았다. 기존 trusted-single-owner lab의 결과와
새 외부-writer 배제 보장을 구분한다.

## 결과

[ADR-F1](ADMISSION_FENCE_CUSTODY_ADR.md)에 권한을 가진 외부 writer의
생성 객체 교체, 검사 뒤 task 주입, 제거 이름 교체라는 세 source-level 반례를 기록했다.
실제 공격을 실행하거나 현재 노트북에서 악성 process를 관측했다는 뜻은 아니다.
원본 FD와 추가 snapshot만으로는 외부 actor의 mutation authority를 회수하지 않는다.

선택한 후속 구조는 보호된 host principal/동등한 강제 정책, 신뢰된 factory,
E 전용 parent P다. F가 P를 제공하고 E가 내부 D를 직접 생성한다.
D를 factory가 생성해 전달하는 구조를 E-created custody로 부르지 않는다.
OS 배제는 P 생성 전부터 refs·in-flight 결과·alias의 확인된 retirement까지 지속되어야 한다.
현재 Delegate=yes, UID1000, W_OK 또는 Python class를 그 집행 증거로 쓰지 않는다.

현재 host binding과 집행 backend는 미구현/UNAVAILABLE다. broker 종료·expiry로
권한이 다시 열리거나 principal이 재사용되면 안 된다는 의무도 아직 구현하지 않았다.
readonly mount, namespace containment, 외부 writer/async drain은 계속 미구현/미검증이다.

## 작업 공간과 revision

- 제품 clone: main 4b77b31dd23010f2d2b394466d88b04a4a2720e2, CLEAN. 원격 최신 main이라고 주장하지 않는다.
- 기존 연구: research/native-e-local 9545d5422096fced078be1243cee98310499d25f, CLEAN.
- 내부 D 이전 ref: research/native-e-internal-d 694604e0722373d6666600e202e454b79a9d3d02, 보존.
- 이번 branch: research/native-e-admission-design, 기존 isolated linked worktree에서 새로 분기.
- Windows의 기존 Carrot 작업 트리는 수정하지 않았다.
- Ubuntu-24.04는 승인된 비대화형 WSL 경로로 사용했다. 현재 kernel/EUID는 제한된 로그에 기록했다.
  이번에 systemd/user-manager 위임이나 현재 runtime 자격을 새로 점검·인정하지 않았다.

## 산출물과 변경 범위

- ADMISSION_FENCE_CUSTODY_ADR.md: 위협 모델, source 공백, 선택지, F1 의무12개,
  원본 live handoff, one-shot lifecycle, 미래 adversarial cases T01–T15.
- evidence_admission_design.json: DESIGN_ONLY 상태, 미구현·미실행과 보존 결과.
- 본 보고서 및 독립 설계 리뷰 기록.
- 기존 PLAN.md/PROGRESS.md에 이번 단계만 append.

src/, tests/, pyproject.toml 및 이전 보고서/evidence를 포함한31개 파일의 SHA256을
작업 시작에 고정하고 종료 때 대조한다. 이 설계의 근거는 그 base source다.
기존 내용은 바꾸지 않는다. 현재 코드가 F1을 집행한다고 선언하는 새 boolean/provider는 없다.

## 실행한 조회와 검증

실제 Windows→Linux 진입은 다음 명령을 사용했으며, 스크립트는 stdin으로 전달했다.

~~~text
wsl.exe --distribution Ubuntu-24.04 --exec /usr/bin/python3 -I -B -
git rev-parse HEAD
git branch --show-current
git status --porcelain
git log -1 --format=%H %s
git diff --check
git diff --name-only
git rev-parse research/native-e-internal-d
~~~

위 Git 조회와 제한된 Python 파일 읽기/SHA256 대조는 exit0이었다.
인계 스크립트 첫 시도는 porcelain 출력 앞 공백을 strip해 PLAN.md를 LAN.md로 읽는
자체 guard 오류로 commit 전에 exit1이었다. 앞 공백 보존으로 최소 재현을 수정·확인했다.
그 실패 전에 source/index mutation은 없었다. 제품/runtime 실패로 집계하지 않는다.
이후 git commit은 작성자 설정 부재로 exit128이었다. 전역/저장소 설정을 쓰지 않고
이번 로컬 연구 commit에만 -c user.name=Codex Research 및
-c user.email=codex-research@localhost를 지정한다. 실제 사용자 신원이나 제품 원작자 표기가 아니다.
새 branch 생성은 git switch -c research/native-e-admission-design을 사용했다.
문서·JSON 작성과 새 로그 작성 외에 runtime 파일은 쓰지 않았다.
최종 문서 검사·commit·bundle 명령/exit는 final-verification 로그에 별도로 남긴다.
최종 로컬 commit과 bundle SHA256은 전달 폴더의 FINAL_DELIVERY.json에서 확인한다.
문서 commit은 이번 branch에만 추가하며 push/merge/PR 변경은 하지 않는다.

공개 primary documentation은 kernel cgroup-v2, unlinkat(2), chmod(2), open(2),
user_namespaces(7), Landlock을 읽었다. 각 URL과 주장을 ADR에 연결했다.
systemd255 resource-control 문서 조회는 timeout으로 실패했으며 근거에 포함하지 않았다.
비공개 HF 자료·외부 인증·원격 제품 저장소 조회는 이번 작업에 필요하지 않아 시도하지 않았다.

| 검증 | 이번 결과 | 구분 |
| --- | --- | --- |
| source/test/config/기존 evidence31파일 | 31/31 일치 | 보존 확인, 실행 자격 증거 아님 |
| JSON flags/상태·문서 consistency | PASS_DOCUMENT_CHECKS_ONLY | 문서 검사만 |
| 단위/제품/coverage/lint/build | NOT_RUN_DESIGN_ONLY | runtime 변경 없음 |
| 새 unit/worker/공격 actor | 0/0/0 | OS 실험 미실행 |
| 기존178 harness +2786 product PASS | 역사 기록만 | 이번 실행 수나 신규 PASS로 합산하지 않음 |
| 기존 b2f2d50 UNKNOWN | 그대로 | 새 설계나 outer teardown으로 해제하지 않음 |

## 리뷰

독립 reviewer가 ADR과 관련 base source를 대조했고 중대한 지적은 없었다.
검토 후 ADR bytes는 수정하지 않았다. [리뷰 기록](ADMISSION_FENCE_DESIGN_REVIEW.md)에
정확한 ADR SHA256과 범위를 남겼다. 보고서/JSON 정리와 문서 검사는 author self-review다.
이는 설계 review이며 코드·kernel enforcement 인증이 아니다.

## 유지 상태

provider_registration=UNBOUND. 기존 qualification16종은 available0/UNAVAILABLE다.
아래14개 값은 전부 false로 유지한다.

~~~text
application_authorized
build_execution_allowed
candidate_generation_allowed
device_class_qualified
owner_proposal_allowed
policy_adopted
promotion_authorized
runtime_accepted
runtime_qualified
actual_payload_released
cleanup_allowed
recovery_execution_authorized
H_executed
HREQ004_qualified
~~~

이번에 설치/업데이트/sudo/관리자 승격/설정 변경/서비스 명령/cgroup 쓰기/
Docker/provider/payload/차량 실행/원격 push/PR/외부 업로드를 하지 않았다.
WSL 비대화형 기동은 기존 승인 범위이며 별도 user unit은 만들지 않았다.

## 재검토와 다음 작업 하나

이 설계는 [ADR](ADMISSION_FENCE_CUSTODY_ADR.md), base source,
[evidence](evidence_admission_design.json)를 함께 읽어 재검토할 수 있다.
T01–T15는 미래 acceptance 계획이며 지금 실행할 worker나 승인된 OS 실험 명령이 아니다.

**다음 작업: 전용 host principal 기반 F/E/W 권한 분리의 최소 provisioning·rollback 계획을 작성한다. 적용은 하지 않는다.**
이유는 실제 배제를 집행할 권한 주체·code store·original handoff·quarantine이
아직 정해져 있지 않아서다. 관리자/정책 변경을 포함하는 구체안은 기존 금지 경계를 넘어 자동 적용하지 않는다.
