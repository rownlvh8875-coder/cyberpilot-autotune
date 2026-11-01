"""Original strict decoder consumes only the explicitly separate telemetry."""

from tests.deny_fd_v2.contracts import Capture
from tests.deny_fd_v2_harness.capture import validate_capture as validate_source_capture
from tests.deny_fd_v2_harness.contracts import need

from .assets import TransportAssets
from .contracts import TransportAcquisitionRecord, TransportProcessResult, error_text


def validate_capture(result: TransportProcessResult, case: str, assets: TransportAssets) -> Capture:
    need(
        type(result) is TransportProcessResult and type(assets) is TransportAssets,
        "bound dual context required",
    )
    result.__post_init__()
    assets.__post_init__()
    need(
        result.termination == "EXITED"
        and result.exit_code == 0
        and result.error is None
        and result.telemetry.complete
        and result.console.complete
        and result.telemetry.error is None
        and result.console.error is None,
        "incomplete or failed dual collection",
    )
    return validate_source_capture(result.telemetry.raw, case, assets.base)


class TransportCaptureFailure(ValueError):
    """Read-only evidence properties; Python exception traceback remains mutable."""

    def __init__(
        self,
        reason: str,
        result: TransportProcessResult,
        completed: tuple[TransportAcquisitionRecord, ...] = (),
        *,
        current_record: TransportAcquisitionRecord | None = None,
        acquisition_error: str | None = None,
        persistence_error: str | None = None,
    ):
        error_text(reason)
        need(reason is not None, "failure reason required")
        need(type(result) is TransportProcessResult, "dual result required")
        need(
            type(completed) is tuple
            and all(type(r) is TransportAcquisitionRecord for r in completed),
            "completed records required",
        )
        need(
            current_record is None
            or (
                type(current_record) is TransportAcquisitionRecord
                and current_record.result == result
            ),
            "current record must match evidence",
        )
        error_text(acquisition_error)
        error_text(persistence_error)
        super().__init__(reason)
        self._payload = (result, completed, current_record, acquisition_error, persistence_error)

    @property
    def result(self) -> TransportProcessResult:
        return self._payload[0]

    @property
    def completed(self) -> tuple[TransportAcquisitionRecord, ...]:
        return self._payload[1]

    @property
    def current_record(self) -> TransportAcquisitionRecord | None:
        return self._payload[2]

    @property
    def acquisition_error(self) -> str | None:
        return self._payload[3]

    @property
    def persistence_error(self) -> str | None:
        return self._payload[4]
