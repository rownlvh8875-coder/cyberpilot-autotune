"""Untrusted v2 cross-binding and immutable failure payloads, never admission."""

from tests.deny_fd_v2.contracts import Capture
from tests.deny_fd_v2.validation import check_inventory
from tests.deny_fd_v2.wire import decode

from .assets import validate_bundle
from .contracts import AcquisitionRecord, AssetBundle, case_label, need


def validate_capture(raw: bytes, case: str, assets: AssetBundle) -> Capture:
    case_label(case)
    validate_bundle(assets)
    capture = decode(raw)
    decision = check_inventory(capture)
    need(decision.outcome == "WIRE_DIAGNOSTIC_CONSISTENT", "inventory consistency rejected")
    begin = capture.events[0].values
    need(
        begin[2:4] == (assets.source_revision, assets.source_manifest_digest) and begin[6] == case,
        "capture source/case mismatch",
    )
    expected = 3 if case == "DFD03" else 0
    need(
        capture.events[1].values == (1, expected, 1)
        and capture.events[2].kind == "EXPECT"
        and capture.events[2].values == (1, expected),
        "capture requested policy mismatch",
    )
    return capture


class CaptureFailure(ValueError):
    """Immutable evidence payload; the exception's Python traceback remains mutable."""

    def __init__(
        self,
        reason: str,
        raw: bytes,
        raw_complete: bool,
        completed: tuple[AcquisitionRecord, ...] | list[AcquisitionRecord] = (),
    ):
        need(
            type(reason) is str and 0 < len(reason) <= 4096 and "\0" not in reason,
            "bounded failure reason required",
        )
        need(type(raw) is bytes and len(raw) <= 1024 * 1024, "bounded failure bytes required")
        need(type(raw_complete) is bool, "failure completeness required")
        need(
            type(completed) in (tuple, list)
            and all(type(r) is AcquisitionRecord for r in completed),
            "completed records required",
        )
        super().__init__(reason)
        self._raw = raw
        self._raw_complete = raw_complete
        self._completed = tuple(completed)

    @property
    def raw(self) -> bytes:
        return self._raw

    @property
    def raw_complete(self) -> bool:
        return self._raw_complete

    @property
    def completed(self) -> tuple[AcquisitionRecord, ...]:
        return self._completed
