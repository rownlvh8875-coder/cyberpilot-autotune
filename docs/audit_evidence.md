# Pinned audit evidence

Recorded 2026-10-28. The user corrected the original SHA typo; all official evidence
uses the fixed commit below. Initial supplemental inspection was retained and
confirmed against this same detached checkout. No source text was copied.

## Verified commit metadata

| Field | Value |
|---|---|
| SHA | 588d6b21c21089065a7d9165d6e7a438e8aa6297 |
| Parents | 3537fdbc7d3eb74c48a1202d6289a562e0aa1aee |
| Author | rownlvh8875-coder |
| Author timestamp | 2026-10-26T16:20:36+09:00 |
| Subject | ci(cyberpilot): add exact27 shadow boundary qualification |

Verification: branch ref fetched; cat-file -e <SHA>^{commit} succeeded;
checkout --detach <SHA>, rev-parse HEAD and show metadata agreed.

Separately observed remote feature/cyber-autotune HEAD: 588d6b21c21089065a7d9165d6e7a438e8aa6297.

## Selected source hashes and import edges

SHA-256 hashes identify the inspected files, not copied artifacts or physical evidence.

| Source path | SHA-256 | Direct imports |
|---|---|---|
| openpilot/tools/cyber_autotune/contracts.py | 991891f87fd7f585f0f9e71767164db7be1ca2740c68cffa292c8c6876ba7001 | dataclasses, math, openpilot.selfdrive.controls.lib.cyber_lateral.command_domain, openpilot.selfdrive.controls.lib.cyber_lateral.metrics, re, types |
| openpilot/tools/cyber_autotune/profiles.py | 76843bb6d70fe824bb8c775868f0e71c4b9ad223339d5ea7b119708ac42f3073 | dataclasses, fractions, hashlib, json, openpilot.tools.cyber_autotune.contracts, openpilot.tools.cyber_autotune.policy |
| openpilot/tools/cyber_autotune/policy.py | dd44a07a6c8a3730846ecddbb9202c73a8299a93c9f8b0aacfd1aa431c755578 | dataclasses, enum, openpilot.tools.cyber_autotune.contracts, types |
| openpilot/tools/cyber_autotune/shadow.py | 5be3d1e58e22724c68bacbe0cf3ff8fcb7b45fb8fedce767c90948afc9dbb099 | dataclasses, json, math, openpilot.tools.cyber_autotune.native_protocol, openpilot.tools.cyber_autotune.native_runner, threading, time |
| openpilot/tools/cyber_autotune/native_runner.py | ad80e8ed19d871605771827b09593eebfea5f2c9a7f7486cedf1ed51f83006d0 | dataclasses, json, openpilot.tools.cyber_autotune.native_protocol, os, pathlib, signal, subprocess, sys, time |
| openpilot/tools/cyber_autotune/native_worker.py | c79b75fd0a75d5dc58ebd459d80b89aeeb54bcd849afacd070cd2bace4bed1ac | base64, contextlib, inspect, math, native_protocol, numpy, opendbc.car, opendbc.car.interfaces, opendbc.car.vehicle_model, openpilot.common.constants, openpilot.common.filter_simple, openpilot.common.pid, openpilot.selfdrive.controls.lib.latcontrol, openpilot.selfdrive.controls.lib.latcontrol_torque, openpilot.tools.cyber_autotune.a1_schedule, os, pathlib, source_imports, subprocess, sys, types, worker_resources |
| openpilot/tools/cyber_autotune/replay_input.py | 5b328c8f97ea7dd90d2ed70f12d2f9a62e1bd5ddaec097780822ed4d97dfe9c5 | contextlib, fcntl, hashlib, json, openpilot.tools.cyber_autotune.replay_admission, os, stat, subprocess |
| openpilot/tools/cyber_autotune/archive.py | dc0d3b4f2caf11bf1b24e270a83fcfe240ae0b13a13220d0a49a3111392c3f9d | contextlib, ctypes, errno, fcntl, functools, openpilot.tools.cyber_autotune.archive_codec, openpilot.tools.cyber_autotune.contracts, openpilot.tools.cyber_autotune.profiles, os, pathlib, stat, sys, uuid |
| openpilot/tools/cyber_autotune/synthetic_lateral_gate.py | dc2b770f01125705d36a846aabd1076ca4b589c8b3bb31b26249194f0a55f571 | dataclasses, hashlib, json, openpilot.tools.cyber_autotune.contracts, openpilot.tools.cyber_autotune.synthetic_lateral_closed_loop, pathlib |
| openpilot/selfdrive/controls/lib/cyber_lateral/optimizer.py | 3967788c144d639375570de1d5a8a6e464e2fbb6addf4cc4671ac04073debf22 | dataclasses, math, openpilot.selfdrive.controls.lib.cyber_lateral.experiments, openpilot.selfdrive.controls.lib.cyber_lateral.speed_aware_tune, openpilot.selfdrive.controls.lib.cyber_lateral.steering_rate, openpilot.selfdrive.controls.lib.cyber_lateral.torque_authority, typing |

## Keyword search

Scanned 1147 tracked Python/Markdown files in docs, AutoTune tools,
tools/cyberpilot and cyber controller-library areas. Counts are files containing
the case-insensitive literal or whitespace/hyphen/underscore-separated phrase.
They are discovery evidence, not a claim that each hit implements the concept.

| Term | Matching files |
|---|---:|
| autotune | 1005 |
| auto tune | 0 |
| online | 47 |
| adaptation | 13 |
| learner | 18 |
| learning | 9 |
| proposal | 55 |
| safety gate | 2 |
| sanitizer | 0 |
| rate | 770 |
| rate budget | 0 |
| r policy | 63 |
| shadow | 212 |
| replay | 331 |
| source schema | 25 |
| controller | 410 |
| lateral | 370 |
| longitudinal | 92 |
| rollback | 167 |
| watchdog | 0 |
| persistence | 69 |
| state | 655 |
| candidate | 712 |
| F-60 / F60 | 0 |
| F-61 / F61 | 0 |
| F-62 / F62 | 0 |
| F-63 / F63 | 0 |
| F-64 / F64 | 0 |
| F-65 / F65 | 0 |
| F-66 / F66 | 0 |
| F-67 / F67 | 0 |
| F-68 / F68 | 0 |
| F-69 / F69 | 0 |

## ajouatom/openpilot observed remote heads

Full discovery snapshot; source candidate remains pinned in carrot_integration.md.

| Ref | SHA |
|---|---|
| refs/heads/apilot-c2 | 1f67e47b21d6627ad96b79703b6ddf5f3bd7abab |
| refs/heads/c3-wip | f2118063e379fa7f5e0d1c0364910b79864ca553 |
| refs/heads/carrot | 62d004320d5a8683b919379f16811a832a894cf5 |
| refs/heads/carrot-wip | 604bc0a22733e648ec05b268da1ffaae7db52a69 |
| refs/heads/happymaj11r/carrot-wip-model_selector | 3247d7e633330849bc1022fa62e955577908e4a6 |
| refs/heads/hoya/c3-atune | 0e9c589c1b83027146f909a9cdc306c2c665ceaf |
| refs/heads/janpoo6427/carrot-wip-430-remove | 70a101c22494da56c67eb76f06d983016bc1f633 |
| refs/heads/janpoo6427/carrot-wip-angle | 5f5ca95d68d6ca70510d1745718b625d63a429a7 |
| refs/heads/janpoo6427/carrot-wip-angle2 | 426dda281d874e241aea27e48c807f4f7a32ac69 |
| refs/heads/janpoo6427/carrot-wip-angle3 | c695ae99c47c3611814b00c33047be59b82cbe6a |
| refs/heads/janpoo6427/carrot-wip-lanehighlight | 35c1e574069c7838e158ed618b0614d694c7c72f |
| refs/heads/janpoo6427/carrot-wip-navi | debf171b74acafa5f3688c3441fbe0a3952f598b |
| refs/heads/jominki354/cavdy-alpha | 441edc14b9ccfa62ed4286716d53dd0aeeb10015 |
| refs/heads/jominki354/ytdelete | 598d8e19877d1aec7040d7e5b7639fb74cfd7588 |
| refs/heads/joongyu01/carrot-wip-dev | 465563a4bea081b47242e4bc4a7dc9d74afadf07 |
| refs/heads/joongyu01/cluster-c4-updates | 404929bae09bd2913967e39c3522de42fe961472 |
| refs/heads/thftgr/carrot-egpu | 0bde5f6fbc1bf377c949aa04aa6384d4aadc5b6b |
| refs/heads/thftgr/carrot-egpu-tg | 0f3b1d65f1a2ce457b388aa7a04fd1a80d0c569a |
| refs/heads/thftgr/carrot-wip-x | 1916c32df4bdd916f465ccade0fb2118a931a050 |
| refs/heads/thftgr/carrot-wip-x2 | 2aba878af18bfd32500b5779892f011750c64be3 |
| refs/heads/thftgr/cluster | 506a68db5781ad61295905df9af4c593bf1a438a |
| refs/heads/thftgr/navi-stream | 7bc2584700c9c25aacce4ed550ef29a902664138 |
