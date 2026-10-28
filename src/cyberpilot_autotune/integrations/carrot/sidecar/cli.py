"""Bounded parked-only read-only qualification. No vehicle readiness is declared."""

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any, Never

from cyberpilot_autotune.adapters.carrot_receipt_contract import (
    CarrotSnapshotPolicy,
    StaticVehicleContext,
)

from ..adapter import AdapterConfig, CachePolicy, ProducerAttestation, SteeringPressedCapability
from ..errors import CarrotDependencyUnavailable, CarrotSchemaIncompatible
from ..health import SessionToken
from .config import SidecarConfig, SidecarError, SidecarReason, require, validate_launch_pins
from .diagnostics import format_summary
from .runner import SidecarRunner
from .source import SubMasterSource, open_live_source

CONFIG_KEYS = frozenset(
    (
        "static_context",
        "static_context_digest",
        "baseline_parameters",
        "baseline_epoch",
        "session",
        "cache_policy",
        "snapshot_policy",
        "steering_pressed_capability",
        "allowed_controller_kinds",
    )
)
MAXIMUM_CONFIG_BYTES = 65536


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        # argparse normally echoes untrusted argv; keep only a stable code.
        raise SidecarError(SidecarReason.INVALID_CONFIG)


def _parser() -> Parser:
    parser = Parser(description=__doc__)
    qualify = parser.add_subparsers(dest="command", required=True).add_parser(
        "qualify", help="parked-only bounded read-only diagnostics; JSON config on stdin"
    )
    for flag in ("source-revision", "integration-revision", "contract-basis", "schema-revision"):
        qualify.add_argument("--" + flag, required=True)
    qualify.add_argument("--expected-platform")
    qualify.add_argument("--runtime-platform")
    qualify.add_argument("--poll-timeout-ms", type=int, required=True)
    qualify.add_argument("--maximum-updates", type=int, required=True)
    return parser


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        require(key not in result, SidecarReason.INVALID_CONFIG)
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise SidecarError(SidecarReason.INVALID_CONFIG)


def _config(args: argparse.Namespace, text: str) -> SidecarConfig:
    try:
        require(len(text.encode("utf-8")) <= MAXIMUM_CONFIG_BYTES, SidecarReason.INVALID_CONFIG)
        data = json.loads(text, object_pairs_hook=_pairs, parse_constant=_nonfinite)
        require(type(data) is dict and set(data) == CONFIG_KEYS, SidecarReason.INVALID_CONFIG)
        context = StaticVehicleContext(**data["static_context"])
        policy = CarrotSnapshotPolicy(**data["snapshot_policy"])
        require(
            data["static_context_digest"] == context.digest, SidecarReason.STATIC_CONTEXT_MISMATCH
        )
        require(
            data["baseline_epoch"] == policy.baseline_epoch, SidecarReason.BASELINE_EPOCH_MISMATCH
        )
        require(type(data["session"]) is dict, SidecarReason.SESSION_TOKEN_MISSING)
        token = SessionToken(**data["session"])
        capability = data["steering_pressed_capability"]
        attestation = ProducerAttestation(
            args.source_revision,
            args.integration_revision,
            args.schema_revision,
            data["static_context_digest"],
            data["baseline_epoch"],
            token,
            tuple(data["allowed_controller_kinds"]),
            SteeringPressedCapability(**capability) if capability is not None else None,
            args.runtime_platform,
        )
        adapter = AdapterConfig(
            context,
            policy,
            data["baseline_parameters"],
            CachePolicy(**data["cache_policy"]),
            attestation,
        )
        return SidecarConfig(
            adapter=adapter,
            source_revision=args.source_revision,
            integration_revision=args.integration_revision,
            contract_basis=args.contract_basis,
            schema_revision=args.schema_revision,
            expected_platform=args.expected_platform,
            runtime_platform=args.runtime_platform,
            poll_timeout_ms=args.poll_timeout_ms,
            maximum_updates=args.maximum_updates,
        )
    except SidecarError:
        raise
    except Exception:
        raise SidecarError(SidecarReason.INVALID_CONFIG) from None


def _error(code: str, exit_code: int) -> int:
    try:
        print(
            json.dumps(
                dict(error=code, exit_code=exit_code), sort_keys=True, separators=(",", ":")
            ),
            file=sys.stderr,
        )
    except OSError:
        pass
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    runner: SidecarRunner | None = None
    source: SubMasterSource | None = None
    try:
        try:
            args = _parser().parse_args(argv)
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 0 if exc.code is None else 2
        validate_launch_pins(
            args.source_revision,
            args.integration_revision,
            args.contract_basis,
            args.schema_revision,
            args.expected_platform,
            args.runtime_platform,
        )
        require(args.poll_timeout_ms > 0 and args.maximum_updates > 0, SidecarReason.INVALID_CONFIG)
        try:
            text = sys.stdin.read(MAXIMUM_CONFIG_BYTES + 1)
        except Exception:
            raise SidecarError(SidecarReason.INVALID_CONFIG) from None
        cfg = _config(args, text)
        source = open_live_source(cfg.adapter.attestation.session)
        runner = SidecarRunner(cfg, source)
        for _ in range(cfg.maximum_updates):
            runner.poll_once()
            print(format_summary(runner.diagnostics()))
            if runner.fault is not None:
                raise SidecarError(runner.fault)
        runner.close()
        print(format_summary(runner.diagnostics()))
        return 0
    except KeyboardInterrupt:
        return 0
    except CarrotDependencyUnavailable:
        return _error("DEPENDENCY_UNAVAILABLE", 3)
    except CarrotSchemaIncompatible:
        return _error("SCHEMA_UNAVAILABLE", 3)
    except SidecarError as exc:
        if runner is not None:
            try:
                print(format_summary(runner.diagnostics()))
            except OSError:
                pass
        return _error(exc.reason.code, exc.reason.exit_code)
    except Exception:
        return _error("RUNTIME_INVARIANT_FAULT", 5)
    finally:
        if source is not None:
            source.close()


if __name__ == "__main__":
    raise SystemExit(main())
