"""Test Yale Access Bluetooth Activity sensors."""

from typing import Any
from unittest.mock import patch

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import STORAGE_KEY as RESTORE_STATE_KEY
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_restore_state_shutdown_restart,
    mock_restore_cache_with_extra_data,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion
from yalexs_ble import DoorActivity, LockActivity
from yalexs_ble.const import (
    DoorStatus,
    LockOperationRemoteType,
    LockOperationSource,
    LockStatus,
)

from . import MOCK_UTC_NOW, MockNow, setup_integration


async def test_sensors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    lock: er.RegistryEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test all sensors created by the integration."""
    with patch("custom_components.yalexs_ble_activity.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)


@pytest.mark.parametrize(
    "lock_activities",
    [
        [
            LockActivity(
                timestamp=MOCK_UTC_NOW,
                status=LockStatus.UNLOCKED,
                source=LockOperationSource.PIN,
                remote_type=LockOperationRemoteType.UNKNOWN,
                slot=3,
            ),
            LockActivity(
                timestamp=MOCK_UTC_NOW,
                status=LockStatus.LOCKED,
                source=LockOperationSource.AUTO_LOCK,
                remote_type=None,
                slot=None,
            ),
        ],
        [
            LockActivity(
                timestamp=MOCK_UTC_NOW,
                status=LockStatus.LOCKED,
                source=LockOperationSource.REMOTE,
                remote_type=LockOperationRemoteType.BLE,
                slot=None,
            )
        ],
        [
            DoorActivity(
                timestamp=MOCK_UTC_NOW,
                status=DoorStatus.AJAR,
            )
        ],
        [type("UnsupportedActivity", (object,), {"timestamp": MOCK_UTC_NOW})()],
    ],
    ids=[
        "pin_unlock_then_auto_lock",
        "remote_lock",
        "door_ajar",
        "unsupported_activity",
    ],
)
async def test_sensor_activity_update(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    lock: er.RegistryEntry,
    lock_activities: LockActivity,
    now: MockNow,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test all sensors created by the integration."""
    with patch("custom_components.yalexs_ble_activity.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    def _snapshot(phase: str):
        for entity_entry in er.async_entries_for_config_entry(
            entity_registry, config_entry.entry_id
        ):
            assert entity_entry == snapshot(
                name=f"{entity_entry.entity_id}-{phase}-entry"
            )
            assert entity_entry.disabled_by is None, "Please enable all entities."
            state = hass.states.get(entity_entry.entity_id)
            assert state, f"State not found for {entity_entry.entity_id}"
            assert state == snapshot(name=f"{entity_entry.entity_id}-{phase}-state")

    activity_update = _activity_update_handler(hass, lock)

    for lock_activity in lock_activities:
        activity_update(lock_activity, lock_info=None, connection_info=None)

    _snapshot("activity-received")

    now._tick(2)
    await hass.async_block_till_done()
    _snapshot("post-tick")


RESTORE_STATE_PARAMETRIZED = ("stored_data", "expected_state", "expected_attributes")
RESTORE_STATE_SCENARIOS = {
    "simple": {
        "stored_data": {
            "value": "locked",
            "attributes": {
                "source": "auto_lock",
            },
        },
        "expected_state": "locked",
        "expected_attributes": {
            "source": "auto_lock",
        },
    },
    "no_values": {
        "stored_data": {"value": None, "attributes": None},
        "expected_state": "unknown",
        "expected_attributes": {},
    },
}


@pytest.mark.parametrize(
    RESTORE_STATE_PARAMETRIZED,
    [
        tuple(scenario.get(param) for param in RESTORE_STATE_PARAMETRIZED)
        for scenario in RESTORE_STATE_SCENARIOS.values()
    ],
    ids=RESTORE_STATE_SCENARIOS.keys(),
)
async def test_restore_sensor_save_state(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    config_entry: MockConfigEntry,
    lock: er.RegistryEntry,
    stored_data: dict[str, Any],
    expected_state: str,
    expected_attributes: dict[str, Any],
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test saving sensor/orchestrator state."""
    await setup_integration(hass, config_entry)

    entity_id = "sensor.front_door_operation"
    operation_entity = _activity_update_handler(hass, lock).__self__
    operation_entity._attr_native_value = (
        expected_state if expected_state != "unknown" else None
    )
    operation_entity._attr_extra_state_attributes = expected_attributes or None

    await hass.async_block_till_done()
    await async_mock_restore_state_shutdown_restart(hass)  # trigger saving state

    stored_entity_data = [
        item["extra_data"]
        for item in hass_storage[RESTORE_STATE_KEY]["data"]
        if item["state"]["entity_id"] == entity_id
    ]

    assert stored_entity_data[0] == stored_data
    assert stored_entity_data == snapshot


@pytest.mark.parametrize(
    RESTORE_STATE_PARAMETRIZED,
    [
        tuple(scenario.get(param) for param in RESTORE_STATE_PARAMETRIZED)
        for scenario in RESTORE_STATE_SCENARIOS.values()
    ],
    ids=RESTORE_STATE_SCENARIOS.keys(),
)
async def test_restore_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    lock: er.RegistryEntry,
    stored_data: dict[str, Any],
    expected_state: str,
    expected_attributes: dict[str, Any],
    snapshot: SnapshotAssertion,
) -> None:
    """Test restoring sensor/orchestrator state."""
    entity_id = "sensor.front_door_operation"
    mock_restore_cache_with_extra_data(
        hass,
        (
            (
                State(
                    entity_id,
                    "mock-state",  # note: in reality, this would match the stored data
                ),
                stored_data,
            ),
        ),
    )

    await setup_integration(hass, config_entry)

    state = hass.states.get(entity_id)
    assert state
    assert state.state == expected_state
    assert {
        key: value
        for key, value in state.attributes.items()
        if key not in {"friendly_name", "icon"}
    } == expected_attributes


def _activity_update_handler(hass: HomeAssistant, lock: er.RegistryEntry):
    core_entry = hass.config_entries.async_get_known_entry(lock.config_entry_id)
    data = core_entry.runtime_data
    register_activity_update_call = data.lock.register_activity_callback.mock_calls[-1]
    _name, register_activity_update_args, _kwargs = register_activity_update_call
    (activity_update,) = register_activity_update_args

    return activity_update
