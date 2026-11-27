"""Test component setup."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy.assertion import SnapshotAssertion
from syrupy.filters import props

from custom_components.yalexs_ble_activity.const import CONF_LOCK_ENTITIES, DOMAIN

from . import setup_integration


async def test_async_setup(hass: HomeAssistant):
    """Test the component gets setup."""
    assert await async_setup_component(hass, DOMAIN, {}) is True


async def test_standard_setup(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    lock: er.RegistryEntry,
    device_registry: dr.DeviceRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test standard setup."""
    await setup_integration(hass, config_entry)

    assert lock.device_id is not None
    device = device_registry.async_get(lock.device_id)

    assert device is not None
    assert device.id == lock.device_id
    assert device == snapshot(
        name="device",
        exclude=props(
            # compat for HA DeviceRegistryEntrySnapshot <2025.8.0 and >=2025.6.1
            "suggested_area",
            # compat for HA DeviceRegistryEntrySnapshot <2025.9.0 and >=2025.6.1
            "is_new",
        ),
    )


async def test_renamed_lock_entity(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    lock: er.RegistryEntry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that config entry data is updated when lock entity is renamed."""
    hass.states.async_set(lock.entity_id, "locked")

    assert config_entry.data[CONF_LOCK_ENTITIES] == [lock.entity_id]
    await setup_integration(hass, config_entry)

    entity_registry.async_update_entity(
        lock.entity_id,
        new_entity_id=f"{lock.entity_id}_renamed",
    )
    await hass.async_block_till_done()
    assert config_entry.data[CONF_LOCK_ENTITIES] == [f"{lock.entity_id}_renamed"]


async def test_create_removed_lock_entity_issue(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    lock: er.RegistryEntry,
    issue_registry: ir.IssueRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test we create an issue for removed lock entities."""
    hass.states.async_set(lock.entity_id, "locked")

    await setup_integration(hass, config_entry)

    hass.states.async_remove(lock.entity_id)
    entity_registry.async_remove(lock.entity_id)
    await hass.async_block_till_done()

    assert issue_registry.async_get_issue(
        DOMAIN,
        f"lock_entity_removed_{lock.entity_id}",
    )
