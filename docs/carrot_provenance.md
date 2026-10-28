# Carrot source provenance

Inspected repository: https://github.com/ajouatom/openpilot

Reference: refs/heads/carrot-wip. Exact commit:
`604bc0a22733e648ec05b268da1ffaae7db52a69`. The fetched remote head equals the last observed SHA;
there are zero intervening commits. Target main was separately verified at
09f3f58d9f9f7a59d6f983c4e0536c092aab1a4f. No branch-name-only provenance is used.

## Inspection method and layout

Used git ls-remote, fetch, ls-tree, show and scoped searches against pinned blobs
in the sibling openpilot-carrot-reference checkout. Sources were read as data;
no Carrot process, cereal module, vehicle interface, Params instance or source test
was executed/installed. No reference tracked files, commits, branches or PRs were
modified. Fetching the remote reference did not check out or rewrite its branch.

This pin embeds opendbc_repo as an ordinary Git tree, not a submodule/gitlink;
root opendbc is a symlink to opendbc_repo/opendbc. The actual schema paths are
openpilot/cereal/log.capnp and opendbc_repo/opendbc/car/car.capnp. No independent
opendbc remote SHA is invented. There is no root .gitmodules at this pin.

## Copying and attribution

Copied source code: **none**. No reference source body, algorithm, limits, model,
log, generated schema bindings or binary is included in this target repository.
New documents, policy descriptions and synthetic evidence are independently
written analysis. No adapter/contract mapper is implemented because mandatory
signals remain unresolved. Existing target package code/tests stay unchanged.

Root LICENSE contains an MIT-style permission grant and Comma.ai 2018 copyright;
opendbc_repo/LICENSE has the corresponding grant with Comma.ai 2020 copyright.
Their hashes are recorded below. This is evidence of those files, not a finding
that every embedded/custom/dependency file has audited attribution. The inspected
latcontrol_torque.py names external NN-feedforward work; MEB controlsd comments
reference other forks. Their complete upstream derivation and third-party notices
are unresolved, and no such code is reused. Other embedded trees retain their own
licensing obligations outside this limited audit.

No LICENSE is added or chosen for cyberpilot-autotune. The owner must select its
license and resolve upstream attribution before any later upstream PR/code reuse.

## Inspected file hashes

SHA-256 is over raw Git blob bytes at the exact source commit, independent of
Windows checkout newlines. carrot_source_manifest.json also records blob SHA-1
identities and byte lengths. Searches/ranges focus on the symbols cited in
carrot_signal_contract.md; this is not an audit of unrelated code in these files.

| Actual source path | Raw blob SHA-256 |
|---|---|
| `LICENSE` | `716ce815a0467219c59ec2433e6bce7f32efc45240725c6d3141a52b111d2558` |
| `opendbc_repo/LICENSE` | `6543c4a66b46affddae1b9ae1e1992687f0b7191e74ba3a7235388b9f42a6d13` |
| `opendbc` | `8914f72c601bfe1e2d8bc9c72db822af834201948be3a81a7374ee644c66bec5` |
| `openpilot/cereal/log.capnp` | `42fa4764558d636f91d784ad13b4e15398a8a9a993daf589926c3794ee9d1e86` |
| `opendbc_repo/opendbc/car/car.capnp` | `490441669fd68462b1f59bcaf59d802b23437ce022430d19cb14a4e09f998131` |
| `openpilot/cereal/messaging/__init__.py` | `bb10c4a88e694d7c4e2fa500b92c6d8a9474363297afda3cfba880eea146ad68` |
| `openpilot/cereal/services.py` | `2bb8305cce4070d7fba5caa00ec928bedf13a40da3424d8e16ce23ab632e4ab1` |
| `openpilot/selfdrive/controls/controlsd.py` | `5fc6a9158149a13b3b8786ecf5596f17e037ae9006717f9fa07211ed5f205a6a` |
| `openpilot/selfdrive/controls/lib/latcontrol.py` | `cf57ac5072064072b80f7eb10408ea1e1627fd54d128123fc84cea85d9ab1374` |
| `openpilot/selfdrive/controls/lib/latcontrol_angle.py` | `d01c571d063538f18d47c74b0e8ba6c444fe7c8dff2bb7d8a01d492f48c57dad` |
| `openpilot/selfdrive/controls/lib/latcontrol_pid.py` | `cfa74584b040c8ddb129215894636d2528304ded1c767bdd13679aeadb546d00` |
| `openpilot/selfdrive/controls/lib/latcontrol_torque.py` | `67fb6ecafc4d0ce999e2bbf1b729b5f6cf58a5f787c054e770162e7f2f3629cc` |
| `openpilot/selfdrive/controls/lib/lateral_readiness.py` | `9c18096700082a2c30fb99749946369ff0bc75f7a87d9289d2828316de270092` |
| `openpilot/selfdrive/controls/lib/drive_helpers.py` | `aab41e3bdc94e78ba51acf564bd5271eae08017fbf57b2fe0874f9860805bccf` |
| `openpilot/selfdrive/controls/lib/steer_ratio.py` | `87fc3c01b2c3cfdd0e9df0deacd5dc2416df6edf76b18536d7d2f014d1ce77ee` |
| `openpilot/selfdrive/controls/lib/lateral_planner.py` | `c281ad6cbf56d24ce5777c9d333dd4b995cbd9c36104cd3cd1f7e9ba2d04f341` |
| `openpilot/selfdrive/controls/lib/longitudinal_planner.py` | `d20ec36947c6aefd12b425daa0f8d1fa39d0d273d1da578b13a20b079aad878a` |
| `openpilot/selfdrive/selfdrived/selfdrived.py` | `e160f4588777e9c4bb30550117b349fb70220931a0d3dfa726d8c14cb5d438e9` |
| `openpilot/selfdrive/selfdrived/state.py` | `7081e646c1d183fdc7a4e7bf93e7390d32509e5b398200a319bf7b939b2a6b61` |
| `openpilot/selfdrive/carrot/carrot_controls.py` | `6af0420174b549322dc7d1fa7ee0d9d085ef170dfc35cb74466dd5797fd79c81` |
| `openpilot/selfdrive/car/card.py` | `3bb0538cc4c0473b95eceaaa045b8b7a103dbcf412e16fc247ca1edfdc6cc483` |
| `openpilot/selfdrive/locationd/torqued.py` | `c486912d2ff7d5024043ebf1adfd7ae49dc287679c65fd7be37901bd3a9287cb` |
| `openpilot/selfdrive/locationd/paramsd.py` | `d973bcb4ed39f4828af09b8edf830450ec0e938adef90d76ac6ab59fec3d428b` |
| `openpilot/selfdrive/locationd/lagd.py` | `cd5922709e4686d105a4bef0dadcd56fda6e64eafc9efabb7c1b58a82c99226a` |
| `opendbc_repo/opendbc/car/interfaces.py` | `c6ac888f2c2a85413f98413e5f603cbf4daf3749ed6e3d9c122328656952ca10` |
| `opendbc_repo/opendbc/car/vehicle_model.py` | `f8ca23c2b85c2fc20d7e08271f2e692f26ae38a4fbadfcb621f9998cb65ea39e` |
| `opendbc_repo/opendbc/car/__init__.py` | `f56a23742d37395f5869f9c63a367375e038e2b47966efaed7a9679307c01e5e` |
| `opendbc_repo/opendbc/car/common/conversions.py` | `6691f6e8c74a48175d2497b580573e7164d222414a82ec41814e8fa4a8d138aa` |
| `opendbc_repo/opendbc/car/tesla/carstate.py` | `06950f90e1b2d6ed0d0bb502ca0094ba6f04e43714d84211e218ed4f655f09ae` |
| `opendbc_repo/opendbc/car/hyundai/carstate.py` | `728b74e6f4af1b3e7148d2140a79ab063c8307d6fc9ae2708c029cd916a22b68` |
| `openpilot/selfdrive/pandad/pandad.cc` | `8b1d52adc5809eb663f97d7899bbecd5647cea85fef4f67eb5c1a8b2ee7e1115` |
| `opendbc_repo/opendbc/safety/safety.h` | `a8b2b54271dd1fb3fd7f6998b0473a939dce1bfec56a644fc64cd649cfd825aa` |
| `panda/board/health.h` | `bd8ec57900ea5c717014badc2d281fff8cfeeede0bd985a272bf08f7c1ae1a40` |
| `panda/board/main_comms.h` | `79fe6ea3e7512d227b426db673bb6874d4d0973c21b080f964cdbf57c561839d` |
| `openpilot/common/transformations/README.md` | `3a6f885f5ce95b3c3f3cad4cf63e683f9142f1516ec698c198379c6a66c140f1` |
| `openpilot/tools/joystick/joystickd.py` | `554c62a06b20b8a9f287a86ad29e430c42a312a12353030497489ea199d0a0ba` |
| `openpilot/selfdrive/carrot/realtime/compact_state.py` | `55616d5a4b1070e0cc5c00de88e0291e027981475b06089031f5c9eb66b7b333` |

## Reproduction

For each manifest entry, read git show <commit>:<path> as bytes and compare its
SHA-256, length and git rev-parse <commit>:<path> object identity. Do not hash a
line-ending-converted working copy. Validation results are recorded in
carrot_signal_evidence.md; source content is not duplicated in the target.
