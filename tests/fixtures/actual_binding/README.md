# Historical legacy contract fixture (test only)

legacy_contracts.zip contains exactly nine original Python sources plus their
unchanged SOURCES.json and SHA256SUMS. Archive SHA-256:
a53ddbac195f273843af05e79235985823ecc954f50018d28e5e329297de14c7.
Members are sorted, stored without compression with 1980-01-01 timestamps.
The historical paths in SOURCES.json/pins.py are provenance strings only.
No test resolves or executes the historical VM path.

The actual old SevenInputReference constructor and complete transitive imports
are loaded from this archive in a prepared isolated child to verify exact-type
rejection. This is not a fake lookalike or a runtime dependency. The archive is
not extracted and is excluded from the installed wheel by the src package layout.
All members and original hashes are checked before execution; child assertions
verify all nine loaded module origins. No checkout root is on its source roots.

Known original lint defect: content.py has one Ruff I001 import-order finding.
The prior standalone lint gate covered runtime9 + checks13, not these legacy9.
We preserve rather than silently fix/relabel the original bytes. The archive is
historical test data, not lint-clean active source. Repository-wide Ruff rules
remain unchanged; all new active Python files are linted and formatted normally.
The frozen fixture's legacy algorithms are NOT requalified by this type test.

acceptance-coverage-map.json preserves the original 56 scenario meanings while
updating test paths. Old execution status/evidence is explicitly historical.
Repository runs and their exact head are reported separately; a mapping is not
test execution evidence and synthetic success is never runtime qualification.
