# Exact-R native build dependency inventory (not acquired)

Source metadata and hashes are in
[the evidence manifest](evidence/native_build_verification_sources.json).
This is a design inventory, **not an offline artifact-closure manifest**.

## Locked inputs

R pyproject requires Python `>=3.12.3,<3.13`; uv.lock version1/revision3 has121
package records and SHA-256
`3d3a7e31e04e654a86ed332fb8b97d67f5648905ee0b276bc53cfbc87fe5dcdf`.
Selected exact locked versions: numpy2.5.3, Cython3.3.0, SCons4.11.1,
setuptools84.0.0, pycapnp2.1.0, comma-deps-acados0.2.2.post103,
comma-deps-json1120170411.0.post103, comma-deps-raylib6.0.0.1.post103 and
comma-deps-catch22.13.10.post96. The lock was parsed/hash checked, not resolved or
installed. The lighter native-cpu CI's Cython3.2.9 is not interchangeable.

These VCS wrappers pin commits, despite release-branch names in source metadata:

| Package | Locked commit |
|---|---|
| bootstrap-icons | `c4393237b34dffdb325b5e72b24712c5ca074e03` |
| bzip2 | `90b7fefbe37fc2ca26597e6e9e0035dd386effa1` |
| capnproto | `05582563f2fdf6638a550fef61b129a2fb288d05` |
| eigen | `40e5d76de1b33a86c5181b63db6782d8f06da1da` |
| ffmpeg | `b9732165bcf5a3fab83b05994187802a0d115b6e` |
| gcc-arm-none-eabi | `15a616d4f08f6b8ecaa9b2390c75d2fe0c0fffb8` |
| git-lfs | `f77417aad13a05b03bb2696a0b5a124f339d117b` |
| imgui | `c5c108b23a2e0346480d7f4c4981bf6ec7ba9054` |
| libjpeg | `2d69723fe445dadc68ceb9072510a505111b64a7` |
| libusb | `8daf8079f98809ef4674177bca915a0a81eac52f` |
| libyuv | `28c3c2a2444232aeeaf989c33fd333ce74e6fc90` |
| ncurses | `e33e7f648009ad97638b1a0a373a06a05526c040` |
| zeromq | `0f7d2b9121cc30c0e377717fc1db52205a8e4c80` |
| zstd | `b2b10636beba0384eada30979651b4ca7cf919ff` |
| metadrive-simulator | `2716f55a9c7b928ce957a497a15c2c19840c08bc` |

This table is not all121 records or proof their platform artifacts exist. Gate A
must enumerate the complete platform-selected lock graph (including test tooling
such as the pytest-xdist fork), PEP517 build dependencies, Git trees, native
archives downloaded by wrapper hooks, registry wheels/sdists and their hashes.
No mutable VCS revision may be substituted when a pinned object is unavailable.

## Closure categories and open gates

| Category | Needed for selected full-host profile | Still to acquire/verify |
|---|---|---|
| Native source | complete R blobs/trees, seven-entry preserved patch, executable/symlink modes | current cache is partial; complete offline materialization and raw checksums |
| Base/system | immutable Ubuntu24.04 amd64 image; signed repository snapshot and exact installed package versions | image digest, package archives/manifest, license/source provenance |
| Python/bootstrap | exact Python3.12 patch/ABI, uv executable, hatchling/build hooks | artifact digests, CA trust, complete offline reinstall |
| Python/VCS | uv.lock all-extras platform graph, transitive build inputs | hash-checked payloads plus wheel/native-library architecture/ABI |
| Native libraries | vendored wrapper libraries, acados, Cap'n Proto compiler, Eigen, JSON11, ffmpeg, JPEG/YUV, zmq/zstd, bz2/ncurses, raylib, libusb, Catch2 | library paths/version closure and target-by-target link compatibility |
| Host tools | C/C++ compiler, linker/binutils, make/pkg-config, Cython, fonts/graphics/Qt/system dev libraries from source setup | exact versions, headers, font/codegen tools, no relaxed Werror/link whitelist |
| Models | source driving/monitoring ONNX; tinygrad CPU:LLVM compiler/library/host features | model payloads/hashes, LLVM shared-library ABI and offline compile support |
| Firmware | locked ARM GCC13.2.1, objcopy/objdump, crypto/signing tool dependencies, source debug fixtures | native archives/executables and safe debug-only build graph; no production cert |

Ubuntu setup requests build-essential, Qt5/OpenGL/dev headers, protoc/zmq/lz4/zstd,
Python dev and other tools. Loggerd/host replay link additional multimedia/VA/DRM
libraries. Read **all** exact setup/SCons manifests during A; this category table
does not replace their package list. In particular source setup alone does not
prove a suitable LLVM shared library is installed. Tinygrad's generated loader
tries LLVM/LLVM21…14 on Linux; a candidate library is not compatibility proof.

R setup scripts are evidence, not the approved bootstrap program. `tools/setup.sh`
clones a different upstream/master and installs hooks/aliases. `op.sh setup`
dispatches dependency setup; `setup_dependencies.sh` installs/updates uv, invokes
`uv sync --frozen --all-extras` and mutates host udev rules. Do not run these on
the managed host or treat them as immutable/offline. Build an external, reviewed,
digest-pinned preparation recipe; record differences from upstream setup. Native
source/lock/build checks stay unchanged. Image preparation itself is future work.

## Source layout and model payload metadata

R's recursive tree has no160000 gitlinks; named dependencies are vendored trees
with tracked120000 symlinks at msgq, opendbc, rednose, teleoprtc, tinygrad and two
other paths. Reproduce every tracked mode/target; do not flatten symlinks or reuse
a Windows checkout's line endings. `.gitattributes` has no general LFS filter;
that does not prove the partial local cache contains all payloads.

Model tree `d77de9958340d65029fae23833eabd7e4f5a50a7` has these GitHub-reported
regular blob metadata (payloads **not downloaded**, no raw SHA-256 asserted):

| Path under openpilot/selfdrive/modeld/models | Git blob | Bytes |
|---|---|---:|
| dmonitoring_model.onnx | `3edf5aa76b9637e13afd90d079993ebd4abcd5e1` | 7844499 |
| driving_supercombo.onnx | `1aac351ca371f1f68c565470e07a530c7a65f185` | 60792584 |

Default full-host model compilation must work entirely from sealed inputs.
Optional USB/eGPU external large-model delivery is excluded, not a download
fallback. Assets beyond these two models (fonts, tables, transitive codegen data)
must also be enumerated. Model-size metadata does not bound peak memory/disk.

## Future seal receipt

Use `offline-native-build-inputs-v1` JSON with explicit null/unavailable and no
NaN/Inf/duplicate keys. Required fields: profile, R/patch/tree/registration IDs,
CyberPilot checkout SHA, raw lock/pyproject hashes, platform/Python ABI,
image manifest+config digests, uv/toolchain/library versions+raw artifact digests,
complete source object availability/modes, per-artifact category/path/origin/
immutable revision/size/SHA-256, package build-hook audit, allowed environment/
write-path/action manifest, resource budget, preparation log hashes and license
provenance. Clock/host observations are context, not identity or vehicle data.

Canonical content digest: sorted compact UTF-8 JSON, explicit unknowns, no floats
for exact integer byte/time fields, excluding the digest field itself. It proves
content identity only, never authenticity, runtime safety or authority. No
credentials, private keys, VIN, routes, device IDs or empirical driving data.
Receipt validation/rebuild tooling and acquired manifest do not exist yet.
