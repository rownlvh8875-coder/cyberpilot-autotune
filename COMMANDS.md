# 실제 명령 / 결과
모든 Linux 명령은 Windows wsl.exe --distribution Ubuntu-24.04 --exec /usr/bin/python3 -I -B -
의 비대화형 orchestrator에서 subprocess argv로 실행했다. 전역 설정·sudo·기존 서비스 작업 없음.

| 명령/작업 | exit / 결과 |
| --- | --- |
| git clone -- https://github.com/rownlvh8875-coder/cyberpilot-autotune <새 product 경로> |0|
| git rev-parse HEAD; git branch --show-current; git status --porcelain=v1 (별도 호출) |0 /4b77b31d, main, CLEAN|
| rg --files (Linux) |127-equivalent FileNotFoundError; git ls-files fallback0|
| exact3 systemd paths vs dpkg-query --control-show systemd md5sums |0 /3MATCH, 로컬DB 비교일 뿐|
| python3 -m venv .venv |1 /ensurepip 없음|
| python3 -m venv --without-pip .venv |0|
| 기존 Windows 번들 pip Python 패키지를 새 venv로만 복사 |성공, 시스템 설치 없음|
| .venv/bin/python -m pip install -e .[dev] |초기 src 부재1; 새 src 생성 뒤0|
| python -m pip install <새 product build copy>[research] |0 /원본 clone 수정 없이 wheel install|
| pytest 최초 protocol/handles/runner |2 /모듈 부재 RED, 이후20PASS|
| pytest native 신규13 |1 /binary 부재 RED, 이후13PASS|
| cc -std=c11 -O2 -Wall -Wextra -Werror -o <fixed supervisor> supervisor.c |0|
| 수명주기/factory/exit semantics/sticky uncertainty/독립리뷰/원본OFD 신규 실패 테스트 |각1 RED, 수리 뒤 GREEN; logs/red-*.txt|
| pytest -q (연구 harness 전체) |최종코드123PASS/0FAIL/0SKIP, 반복건수 미가산|
| pytest -q -p no:cacheprovider --basetemp=<새 logs>/product-temp --cov=cyberpilot_autotune --cov-report=term-missing --cov-fail-under=90 |0 /기존2786PASS/0FAIL/0SKIP,98.50%|
| python -m ruff check --no-cache . (product) |0|
| python -m ruff format --check --no-cache . (product) |0 /323files|
| python -m mypy --cache-dir <새 logs>/product-mypy src/cyberpilot_autotune |0 /75files|
| coverage report --include=*/safety/* --fail-under=95 |0 /100%|
| coverage report --include=*/core/residual.py --fail-under=95 |0 /97.85%|
| coverage report --include=*/replay/* --fail-under=95 |0 /98.48%|
| python -m cyberpilot_autotune.replay.cli verify-all tests/fixtures/replay |0 /4golden|
| python -m build (product build copy 및 harness) |각1 /ensurepip 없음|
| 전용 venv pip install setuptools>=77 wheel |0|
| python -m build --no-isolation (동일 두 소스) |각0 /sdist+wheel|
| python -m ruff check .; ruff format --check .; mypy src/native_e_lab (각각 별도 호출) |각0 /연구 코드|
| 새 wheel venv 생성 --without-pip; pip --python <새 venv> install --no-deps <연구 wheel> |각0|
| fresh wheel python -I -B -m native_e_lab.build_native; run_fixed() |각0 /고정worker완료|
| cc --coverage -O0 -fprofile-abs-path; 기존 native13 계측 복사본 pytest; gcov -b -c |각0 /lines82.35%,branches executed78.41%,taken51.70%|
| same-process SYS_kcmp(KCMP_FILE), factory 원본 vs dup |0 /result0 errno0; 설정/권한 변경 없음|
| systemctl --user show --property=Version (현재 UID bus) |0 /255.4-1ubuntu8.18|
| 첫 factory systemd-run --user --pipe --wait --collect ... gate |0 /manager6상한+kernel4상한 확인 뒤 synthetic완료, 초기commit전 결과|
| Git 연구 전용 init -b research/native-e-local; add; local commit |0 /원격push 없음|

최종 code commit 이후 bounded lab 재검증, 최종 검사/commit은 final report 및 logs/final-*에 기록한다.
unit 이름·호스트명·전체 환경변수·자격증명·private 데이터는 수집/출력하지 않았다.
sudo/apt/daemon-reload/restart/shutdown/Docker/provider/H/차량/PR8/9 작업은0회다.
