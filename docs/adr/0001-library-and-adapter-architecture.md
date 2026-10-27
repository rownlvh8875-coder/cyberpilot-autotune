# ADR 0001: Independent library and read-only adapter

Status: accepted for Phase 0-4, following the supplied architecture.

Use src layout, standard-library runtime dependencies and immutable typed
contracts. Keep all openpilot/cereal types outside core, safety and runtime.
Only an adapter Protocol is defined now. No production adapter is implemented.

Copying the monolithic offline tooling would import native worker, vehicle
parameter, filesystem and process concerns. A library plus a later optional
adapter trades integration convenience for independent tests and small PRs.

Python floor: >=3.12.3,<3.13. Both inspected ajouatom branches' pyproject.toml
declare this range. carrot-wip CI uses setup-python 3.12. CyberPilot's inspected
HEAD declares the same range and .python-version is 3.12.13. The corrected pinned
CyberPilot object equals that inspected HEAD and its version is verified. Local
validation uses the available CPython 3.12.14; CI also tests the minimum 3.12.3.
There are no runtime third-party dependencies or vehicle-specific constants.
