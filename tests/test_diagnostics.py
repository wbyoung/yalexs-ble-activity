"""Test Yale Access Bluetooth Activity diagnostics."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator
from syrupy.assertion import SnapshotAssertion
from syrupy.filters import props

from . import setup_integration


async def test_entry_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    config_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test config entry diagnostics."""
    await setup_integration(hass, config_entry)

    assert await get_diagnostics_for_config_entry(
        hass, hass_client, config_entry
    ) == snapshot(
        exclude=props(
            "id",
            "device_id",
            "entry_id",
            "created_at",
            "modified_at",
            "expires_at",
            "config_entries",
            "config_entries_subentries",
            "primary_config_entry",
        )
    )
