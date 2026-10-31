# PR25/33 strict-input 수정 설계 결과

`STRICT_INPUT_CORRECTION_DESIGN_READY`

이번 결과는 설계 문서와 두 개의 독립 구현 계획입니다. strict 함수, runtime
producer, 원본 수정, 호출부 전환을 구현하지 않았습니다. 아래 테스트는 **기존
회귀 및 원인 확인**이며, 미구현 strict 함수가 통과했다는 뜻이 아닙니다.

## 기준과 재현

Source base/PR49: `1d3c7622603ad402e4f5d1ddb23a77f4d267a6b4`.
main: `a5d3514f23797829eb58d08c638b22cf4dd30c8a`.
기존 Open/Draft PR36개를 작업 시작 시 API로 확인했습니다. 기존 PR 본문은
독립 검증 근거로 사용하지 않았습니다.

| 지적 | 실제 확인 | 해석 |
| --- | --- | --- |
| PR25 | ASCII·한글·U+1F600 parse/digest 성공; lone U+D800/U+DFFF parse 성공 후 UnicodeEncodeError | parse와 digest admission 불일치; ValueError 하위 예외로 이미 fail-closed, 권한 우회 입증 아님 |
| PR33 | 네 limit을 각각 float 동등값으로 바꿔도 validate_schema 성공 | 정확한 int 타입 검사 부족; 상한이나 값 자체 변경 아님 |
| 기존 거절 | members=True/None/15/"16" 거절 | 기존 거절을 그대로 유지해야 함 |

재현은 hand-authored synthetic fixture와 frozen schema의 메모리 사본만 사용했습니다.
새 driving data, kernel build, guest/driver/device/차량 실행은 없습니다.

최소 재현 명령(원본을 변경하지 않음):

```python
import json

from compatibility.native_containment.contracts import canonical_digest, parse_synthetic_case
from tests.audit.validate_guest_input_handoff_design import load, validate_schema
from tests.fixtures.native_containment import synthetic_case

data = synthetic_case()
data["actor_id"] = data["events"][0]["actor_id"] = chr(0xD800)
case = parse_synthetic_case(json.dumps(data))  # succeeds on frozen source
try:
    canonical_digest(case)
except UnicodeEncodeError:
    print("PR25: parse accepted; digest rejected")

schema = load("schema")
schema["limits"]["members"] = 16.0
validate_schema(schema)  # succeeds on frozen source
print("PR33: float-equal members accepted")
```

## 정확한 source binding

아래 값은 source base의 기존 파일입니다. 설계 작성으로 바꾸지 않았습니다.

| path | Git blob SHA-1 | SHA-256 |
| --- | --- | --- |
| compatibility/native_containment/contracts.py | ef77d685d4824b1fff60e1bd6c7fcf480800fac4 | 0ad5b72deba865cb3dccd9db63cf29ffbdce69a60e5f7d453171c73f6d8e8047 |
| compatibility/native_containment/validation.py | 4b7829abdbcc9b56274ac3115ce3afcb2b9ad575 | cb472175637dc031cd6bac5d3d6f6f7537e560294b575cc5eb71d2648986a085 |
| tests/audit/validate_guest_input_handoff_design.py | 8da2097710dd04c1a181917a72d56dfc6ed66de2 | 6b63d81819f7a1148b0fe29589c4bfe38537a5f013e47dc2e2ec8cea60eec263 |
| tests/architecture/test_guest_input_handoff_boundary.py | e46285a52b5d2ec803bc774f0997a7cd652bdf90 | 1a33eb8a18be13e862ed59534eeb5a922ebd083696a0de720779a3602f709ff5 |
| tests/architecture/test_epoch_decoder_bridge_boundary.py | 2dc174ed9d9a4f75e58ef816456b02528864290c | ccc55cbda8cdb9985b5d915122a9b71529dbafa954ef257f02ce4a733767b06f |
| docs/evidence/guest_input_handoff_design_schema.json | 4467fbbc3a3294a930d7effb028a80b8e59ce40b | 1a5abd7da64812108bb71782a77fb4dcb95405b4da58878139ecc3d6c3c40e6a |

## 선택한 수정 경로

원본 직접 변경은 frozen history guard와 충돌하고, compatibility 아래 신규 파일도
기존 whole-subtree guard에 막힙니다. 승인되지 않은 guard 예외나 schema 복제·승격
대신 새로운 tests 전용 strict facade를 설계했습니다.

- PR25: parse 반환 전 canonical UTF8 가능성을 검증하고, UnicodeEncodeError만
  안정된 ValueError로 정리. 유효한 Unicode의 기존 digest/decision은 보존.
- PR33: 네 limit에 exact dict/int/key/value 검사 후 기존 validate_schema 전체 호출.
  int 변환·metadata 수정·legacy 검사 생략 없음.
- caller는 strict 함수를 명시적으로 선택해야 합니다. 원본 호출부를 자동 교체하거나
  기존 API의 결함이 해소됐다고 주장하지 않습니다. 채택은 별도 검토 과제입니다.

선택과 비용: 기존 checkout의 새 branch 사용(격리 약화), 추가 전용 gate 선택
(legacy 호출부 미수정), tests namespace 사용(runtime/default 경로에 자동 적용 안 됨),
원본 digest·schema 유지(새 profile은 validation identity일 뿐 새 evidence 자격 아님).

## 문서와 검증

- 설계: `docs/superpowers/specs/2026-10-31-history-preserving-strict-input-design.md`
- PR25 계획: `docs/superpowers/plans/2026-10-31-strict-containment-input.md`
- PR33 계획: `docs/superpowers/plans/2026-10-31-strict-handoff-limits.md`
- 작성 전 전체 회귀3944PASS38.05s; 관련 회귀356PASS0.56s.
- 기존 handoff audit: 66 synthetic cases, 6 consistent, 7 source files/11 ranges;
  overall BLOCKED, runtime_producer_implemented/runtime_qualified 및 모든 권한 false.
- 정확한 final head 회귀·내부 설계 검토·CI는 실제 완료 후 새 Draft handoff에 기록.
  내부 AI 리뷰는 registered GitHub approval/독립 인간 승인과 다릅니다.

## 남은 차단과 다음 과제

`STRICT_CONTAINMENT_ENTRYPOINT_NOT_IMPLEMENTED`
`STRICT_HANDOFF_ENTRYPOINT_NOT_IMPLEMENTED`
`LEGACY_CALLERS_UNMIGRATED` / `PR25_PR33_FINDINGS_OPEN`

PR34 DENY-FD 기록, PR9 evidence expiry 정책, 기존 source/build-closure 및
runtime/lifetime/publication/all-writer/copy-cut/loss/perturbation/empirical/
fingerprint/watchdog/executor/application 차단은 그대로입니다. 권한은 모두 false.
기존 PR/main 수정·병합·Ready·retarget·rebase·force/shared push 없음.

다음 단일 추천 작업: PR25 strict-containment test-only facade의 계획대로 구현.
이 설계 작업에서는 자동 시작하지 않습니다. 구현이 끝나더라도 원본 caller adoption
전에는 PR25 finding을 CLOSED로 바꾸면 안 됩니다.
