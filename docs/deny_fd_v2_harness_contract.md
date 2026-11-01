# DENY-FD v2 fixed isolated harness

Local implementation scope: a separate test-only harness, not actual acquisition.
The exact design and22-path implementation plan live under docs/superpowers/.
Fixed M2 producer bytes and all v1 sources/captures remain unchanged. P4 routes
only the new exact scope; the original19-path node replays original base source.

Default CLI/import/test/build must never launch QEMU or the probe. A future
explicit guest diagnostic has six fixed cases, pinned VM/probe/source/image
identities, no caller command/payload/VM override and bounded retained raw output.
All decisions remain BLOCKED and nine operational permissions remain false.
No actual guest/capture or runtime/watchdog/application qualification is claimed.

Status: implementation in progress; no readiness claim at preregistration.
