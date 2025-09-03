"""Yale Access Bluetooth Activity test shared functionality."""

from __future__ import annotations

import datetime as dt
from typing import Any
from unittest.mock import Mock

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.yalexs_ble.const import DOMAIN as YALEXSBLE_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

ZHA_DOMAIN = "zha"
MOCK_UTC_NOW = dt.datetime(2025, 5, 20, 10, 51, 32, 3245, tzinfo=dt.UTC)


class _ANY:
    def __repr__(self) -> str:
        return "<ANY>"


ANY = _ANY()


class MockNow:
    def __init__(self, hass: HomeAssistant, freezer: FrozenDateTimeFactory):
        super().__init__()
        self.hass = hass
        self.freezer = freezer

    def _tick(self, seconds) -> None:
        self.freezer.tick(dt.timedelta(seconds=seconds))
        async_fire_time_changed(self.hass)


async def setup_integration(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Set up the component."""
    config_entry.add_to_hass(hass)
    await setup_added_integration(hass, config_entry)


async def setup_added_integration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> None:
    """Set up a previously added component."""
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


def add_mock_lock(
    hass,
    entity_id,
    device_attrs: dict[str, Any] | None = None,
) -> er.RegistryEntry:
    """Add a lock device and (some) related entities.

    Returns:
        The created lock entity.
    """
    domain, object_id = entity_id.split(".")
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    mock_runtime_data = Mock()
    mock_runtime_data.title = " ".join(object_id.capitalize().split("_"))
    mock_runtime_data.lock.address = f"mock-address:{object_id}"
    mock_runtime_data.lock.lock_info.serial = f"mock-serial:{object_id}"
    mock_runtime_data.lock.lock_info.manufacturer = f"mock-manufacturer:{object_id}"
    mock_runtime_data.lock.lock_info.model = f"mock-model:{object_id}"
    mock_runtime_data.lock.lock_info.firmware = f"mock-firmware:{object_id}"
    mock_config_entry = MockConfigEntry(
        title=" ".join(object_id.capitalize().split("_")),
        domain=YALEXSBLE_DOMAIN,
        data={},
    )
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.runtime_data = mock_runtime_data
    device_entry = device_registry.async_get_or_create(
        name=mock_config_entry.title,
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(YALEXSBLE_DOMAIN, f"mock-serial:{object_id}")},
        **(device_attrs or {}),
    )
    return entity_registry.async_get_or_create(
        domain,
        YALEXSBLE_DOMAIN,
        object_id,
        suggested_object_id=object_id,
        device_id=device_entry.id,
        config_entry=mock_config_entry,
    )
