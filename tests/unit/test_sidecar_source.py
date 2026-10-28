"""Actual receive-slot semantics with reader doubles; schemas are checked separately."""

from dataclasses import replace

import pytest

from cyberpilot_autotune.integrations.carrot.sidecar.config import SidecarError
from cyberpilot_autotune.integrations.carrot.sidecar.source import SubMasterSource
from tests.fixtures.carrot_adapter import session
from tests.fixtures.carrot_readers import samples
from tests.fixtures.sidecar import ScriptedSubMaster


def test_updated_topics_deliver_once_in_source_order_and_never_reuse_latest():
    cc, cs, co = samples()
    sm = ScriptedSubMaster([(co, cs, cc), ()])
    source = SubMasterSource(sm, session())
    copied = []
    source.poll(7, lambda value: copied.append((value.topic, value.log_mono_time_ns)))
    source.poll(7, lambda value: copied.append((value.topic, value.log_mono_time_ns)))
    assert copied == [
        ("carControl", cc.log_mono_time_ns),
        ("carState", cs.log_mono_time_ns),
        ("carOutput", co.log_mono_time_ns),
    ]
    assert sm.timeouts == [7, 7]


@pytest.mark.parametrize("field", ["seen", "alive", "freq_ok", "updated"])
def test_every_actual_health_flag_is_copied_without_true_substitution(field):
    cc, _, _ = samples()
    health = replace(cc.transport_health, **{field: False})
    sm = ScriptedSubMaster([(replace(cc, transport_health=health),)])
    source = SubMasterSource(sm, session())
    result = []
    source.poll(1, result.append)
    if field == "updated":
        assert not result
    else:
        assert getattr(result[0].transport_health, field) is False
        assert not result[0].transport_health.healthy


def test_outer_event_valid_is_the_actual_submaster_valid_not_receipt_validity():
    _, _, co = samples()
    source = SubMasterSource(ScriptedSubMaster([(replace(co, event_valid=False),)]), session())
    result = []
    source.poll(1, result.append)
    assert result[0].event_valid is False and result[0].transport_health.valid is False


@pytest.mark.parametrize(
    "field", ["simulation", "ignore_alive", "ignore_average_freq", "ignore_valid", "services"]
)
def test_simulation_ignore_shortcuts_or_extra_topics_are_unsupported(field):
    sm = ScriptedSubMaster([])
    setattr(sm, field, True if field == "simulation" else ["extra"])
    with pytest.raises(SidecarError, match="UNSUPPORTED_ENVIRONMENT"):
        SubMasterSource(sm, session())


@pytest.mark.parametrize("field", ["logMonoTime", "valid"])
def test_missing_timestamp_or_valid_metadata_is_a_fault_not_a_fabricated_value(field):
    sm = ScriptedSubMaster([samples()])
    update = sm.update

    def broken(timeout):
        update(timeout)
        getattr(sm, field).pop("carControl")

    sm.update = broken
    with pytest.raises(SidecarError, match="INVALID_SOURCE_METADATA"):
        SubMasterSource(sm, session()).poll(1, lambda sample: None)


def test_close_is_idempotent_and_never_reads_the_closed_source():
    source = SubMasterSource(ScriptedSubMaster([]), session())
    source.close()
    source.close()
    with pytest.raises(SidecarError, match="SOURCE_CLOSED"):
        source.poll(1, lambda sample: None)


def test_unknown_updated_is_a_metadata_fault_instead_of_a_silent_skip():
    sm = ScriptedSubMaster([])
    sm.update = lambda timeout: None
    sm.updated.pop("carOutput")
    with pytest.raises(SidecarError, match="INVALID_SOURCE_METADATA"):
        SubMasterSource(sm, session()).poll(1, lambda sample: None)


def test_session_tag_is_read_only_and_health_shortcut_changes_are_rechecked():
    sm = ScriptedSubMaster([])
    source = SubMasterSource(sm, session())
    with pytest.raises(AttributeError):
        source.session = session(1)
    sm.update = lambda timeout: setattr(sm, "simulation", True)
    with pytest.raises(SidecarError, match="UNSUPPORTED_ENVIRONMENT"):
        source.poll(1, lambda sample: None)
