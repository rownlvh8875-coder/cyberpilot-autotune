# LOCAL ADMINISTRATOR CHANGE REVIEW REPORT

STATUS: REVIEW_BUNDLE_COMPLETE / APPLY_BLOCKED
Base: 8c0058ee8b24e7acd1de8bec248563d623ff60e4
Branch: research/native-e-admin-review
Date: 2026-11-05

## 완료 결과

현재 F/E/W 코드에 맞춘 [관리자 변경 검토안 ADR-A2](ADMIN_CHANGE_REVIEW.md)와
[거래·rollback/quarantine 절차](ADMIN_CHANGE_TRANSACTION.md)를 작성했다.
기존 provisioning plan과 연구 source/report/evidence68개는 그대로 보존했다.
제품 checkout, 기존 branch, 권한·서비스·실제 장치에는 변경을 하지 않았다.

검토 묶음에는 다음이 있다.

| 파일 | 내용 |
| --- | --- |
| [change-manifest.json](research/admin_review/change-manifest.json) | 신규 계정/code/config/intent footprint, 기존 auth DB/backup/cache 영향, 미충족 B01–B10 |
| [request-contract.json](research/admin_review/request-contract.json) | future system bus transient 생성·private stdin FD·단위/type 계약. 실행 payload 아님 |
| [cohort.service.proposed](research/admin_review/cohort.service.proposed) | 미래 service context의 검토용 view. 설치/기동 가능한 현재 unit 아님 |
| [accounts.conf.proposed](research/admin_review/accounts.conf.proposed) | cp-e-lab/cp-w-lab 제안. 숫자 mapping UNAVAILABLE, 미설치 |
| [source-pins.json](research/admin_review/source-pins.json) | frozen 연구 source/context18개 exact SHA. 배포 artifact 승인과 구분 |
| [check_bundle.py](research/admin_review/check_bundle.py) | 고정 파일만 읽는 offline consistency checker. 실행·설치·DBus API 없음 |
| [tests](tests/test_admin_review.py) | unsafe directives/권한·상한/문법·source drift/허위 승인 승격 mutation regression |
| [리뷰 기록](ADMIN_CHANGE_REVIEW_FEEDBACK.md) | 독립 리뷰 Important1/Minor1 및 RED→GREEN 결과 |

## 핵심 설계 결정

future 고정 factory가 local system bus의 StartTransientUnit을 mode=fail로 한 번 요청하고
private E socket endpoint를 StandardInputFileDescriptor(typeh)로 전달하는 안을 선택했다.
bus-client AddRef와 PID1의 FD duplicate·명시적 shutdown/EOF 수명 문제를 포함했다.
영구 service/공개 listener/enable/daemon-reload를 줄이는 방향이다.

PID1이 E를 생성하므로 adapter가 E의 원래 parent/pidfd owner라고 주장하지 않는다.
E가 W를 직접 생성하고 원래 W pidfd를 wait하는 요구는 유지한다.
P는 manager-created, D는 E-created이며 E outside D와 born-in-D를 별도 증명해야 한다.

root-protected persistent attempt.intent는 DENY-only one-shot 제안이다.
기존 leaf·불명확 결과는 재attach/재arm/UID reuse를 허용하지 않는다.
receipt/path/digest로 live 권한을 복구하는 기능이 아니다.
OS-exclusive fence와 kernel alias retirement는 이 기록만으로 증명되지 않는다.

이는 설계 선택이다. 실제 source/backend, local system bus 동작, UID/build/loader/권한 집행은
아직 미구현/미검증이다. systemd255 원문 확인은 현재 Ubuntu 바이너리/정책 인증이 아니다.

## 적용이 아직 막힌 이유

현재 same-UID harness를 root/capability service로 그대로 실행할 수 없다.

- synthetic UID17001/17002/18001/18002가 실제 local principal mapping이 아니다.
- caller-owned image 검사와 root-owned 보호 code store의 전제가 다르다.
- F가 E를 직접 clone하는 구조와 PID1-created E의 provenance가 다르다.
- 현재 W clone에는 CLONE_INTO_CGROUP가 없고 기존 internal-D와 미결합이다.
- UID가 달라진 W에 대한 pidfd signal 권한, original D stop/FD/grant/fence가 별도 문제다.
- cross-UID seal/filter/PDEATHSIG의 실제 적용·denial·retirement 증거가 없다.

따라서 B01–B10을 현재 blocker로 유지했다.
실제 계정·보호 경로·artifact의 존재나 적용 가능성도 이번에 조사했다고 주장하지 않는다.
계정 생성 도구는 기존 인증 DB와 trailing-dash backup 교체, 조건부 nscd cache 영향을 줄 수 있다.
이 전역 영향은 현재 승인되지 않았으며 auth DB/password/backup 내용은 수집하지 않았다.

## 실제 검증

| 항목 | 이번 fresh 결과 |
| --- | --- |
| 신규 offline checker tests | **73 PASS /0FAIL/0SKIP** |
| 전체 연구 regression | **402 PASS /0FAIL/0SKIP** = 기존329 + 신규73 |
| 신규 checker branch coverage | 94.96%, 기준90 유지 |
| 기존 연구 Python coverage | 91.74%, 기준90 유지 |
| Ruff check/format | exit0,51files formatted |
| mypy | 기존9 + 신규1module, exit0 |
| checker CLI | content_check=PASS, apply=BLOCKED, host_commands=NOT_IMPLEMENTED, exit0 |
| 기존 source/tests/config/report/evidence | 68/68 SHA256 보존 |
| PLAN/PROGRESS | 같은 파일 append-only |
| 기존 제품 source/worktree | main4b77b31dd23010f2d2b394466d88b04a4a2720e2 유지, CLEAN |
| 기존 제품2786PASS | 이전 단계 결과, **이번 NOT_RERUN**, fresh 합계에 추가하지 않음 |
| 새 package build/native compiler/UBSan | NOT_RUN, packaging/C/runtime source 변경 없음 |
| 실제 system bus/unit/계정/권한/cgroup lab | NOT_RUN |

전체 연구 회귀는 기존 고정 synthetic child fixtures를 포함한다.
이것을 새 privileged backend/systemd/실차 실험으로 표현하지 않는다.
402개에는 focused73개가 포함되며 따로 더하지 않는다.
이전 리뷰64PASS와 중간 반복 실행도 합산하지 않았다.

환경 관측: WSL Ubuntu-24.04 noninteractive, Linux6.18.33.2-microsoft-standard-WSL2,
x86_64/EUID1000. 새 관리자 기동/실행 자격은 없다.
WSL 호출 간 같은 namespace·process generation이 유지된다고 가정하지 않는다.
기존 venv를 재사용했고 설치·업데이트·sudo/root/관리자 승격은 하지 않았다.

개발 중 missing-checker RED와 fixture parent mkdir 오류를 확인·수정했다.
wrapper quoting 오류는 source 변경 전에 실패했다.
format/type 오류를 수정했고, formatter 수정은 AST 불변도 확인했다.
독립 리뷰의 공백 정규화 및 global backup 영향 누락은 회귀 테스트로 재현해 보완했다.
최종73/402 및 정적 검증은 수정 뒤 결과다.
[독립 리뷰](ADMIN_CHANGE_REVIEW_FEEDBACK.md)는 source/design 수준이며,
수정 뒤 final-tree 독립 재리뷰나 C0/I0 인증을 주장하지 않는다.

## 재실행

새 private basetemp를 사용한다. 기존 evidence 경로를 pytest basetemp로 재사용하지 않는다.

~~~text
.venv/bin/python research/admin_review/check_bundle.py
.venv/bin/python -m pytest -q tests/test_admin_review.py --cov=research/admin_review --cov-branch --cov-fail-under=90 --basetemp=<new-private-path>
.venv/bin/python -m pytest -q --cov=native_e_lab --cov-branch --cov-fail-under=90 --basetemp=<another-new-private-path>
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src/native_e_lab research/admin_review/check_bundle.py
~~~

checker PASS는 내용 일관성만 뜻한다. 실제 OS parser/manager/권한 효과·provenance·승인 증거가 아니다.
원래 local branch와 새 branch를 보존하고 local append-only commit만 만든다.
push/merge/PR/외부 업로드는 없다.
최종 commit/CLEAN/bundle/hash는 Windows 전달본 FINAL_DELIVERY.json에서 확인한다.

## 유지 상태·다음 작업 하나

provider_registration=UNBOUND. 필수16종 available0 / UNAVAILABLE.
기존9개 admission/qualification flag와 actual_payload_released, cleanup_allowed,
recovery_execution_authorized, H_executed, HREQ004_qualified를 합친14개 모두 false다.
새 approval record, payload/차량 실행, 실제 cleanup/recovery 권한을 만들지 않았다.

**다음 작업은 고정 factory의 private-FD/manager-lifecycle backend(A01–A05)를
무권한 fixture로 구현하는 것이다.**
현재 미완료인 것은 실제 source/backend이며 추가 metadata 관측만으로 해소할 수 없다.
그 구현·build·별도 관리자 변경 검토가 준비되기 전에는 실제 OS 적용을 진행하지 않는다.
