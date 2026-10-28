"""Synthetic caller policy and scripted receive slots; no IPC or vehicle values."""

from cyberpilot_autotune.integrations.carrot.sidecar.config import CONTRACT_BASIS, SidecarConfig
from tests.fixtures.carrot_adapter import hyundai_config

TOPICS = ("carControl", "carState", "carOutput")


def sidecar_config():
    cfg = hyundai_config("HYUNDAI_SANTA_FE_2022")
    return SidecarConfig(
        adapter=cfg,
        source_revision=cfg.attestation.source_revision,
        integration_revision=cfg.attestation.integration_merge,
        contract_basis=CONTRACT_BASIS,
        schema_revision=cfg.attestation.observation_schema_revision,
        expected_platform="HYUNDAI_SANTA_FE_2022",
        runtime_platform="HYUNDAI_SANTA_FE_2022",
        poll_timeout_ms=1,
        maximum_updates=4,
    )


class ScriptedSubMaster:
    def __init__(self, frames):
        self.frames = iter(frames)
        self.services = list(TOPICS)
        self.simulation = False
        self.ignore_alive = []
        self.ignore_valid = []
        self.ignore_average_freq = []
        self.seen = dict.fromkeys(TOPICS, False)
        self.updated = dict.fromkeys(TOPICS, False)
        self.alive = dict.fromkeys(TOPICS, False)
        self.valid = dict.fromkeys(TOPICS, False)
        self.freq_ok = dict.fromkeys(TOPICS, False)
        self.logMonoTime = dict.fromkeys(TOPICS, 0)
        self.data = dict.fromkeys(TOPICS, None)
        self.timeouts = []

    def __getitem__(self, topic):
        return self.data[topic]

    def update(self, timeout):
        self.timeouts.append(timeout)
        self.updated = dict.fromkeys(TOPICS, False)
        for sample in next(self.frames, ()):
            topic = sample.topic
            self.data[topic] = sample.reader
            self.logMonoTime[topic] = sample.log_mono_time_ns
            for name in ("seen", "alive", "freq_ok", "updated"):
                getattr(self, name)[topic] = getattr(sample.transport_health, name)
            self.valid[topic] = sample.event_valid


def config_stdin(cfg):
    from dataclasses import asdict

    return dict(
        static_context=asdict(cfg.adapter.static_context),
        static_context_digest=cfg.adapter.static_context.digest,
        baseline_parameters=dict(cfg.adapter.baseline_parameters),
        baseline_epoch=cfg.adapter.attestation.baseline_epoch,
        session=asdict(cfg.adapter.attestation.session),
        cache_policy=asdict(cfg.adapter.cache_policy),
        snapshot_policy=asdict(cfg.adapter.snapshot_policy),
        steering_pressed_capability=asdict(cfg.adapter.attestation.steering_pressed_capability),
        allowed_controller_kinds=list(cfg.adapter.attestation.permitted_controller_kinds),
    )
