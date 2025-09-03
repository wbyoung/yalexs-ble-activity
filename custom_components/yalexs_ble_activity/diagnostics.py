"""Diagnostics support for Yale Access Bluetooth Activity."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

TO_REDACT: set[str] = set()


async def async_get_config_entry_diagnostics(  # noqa: RUF029
    hass: HomeAssistant,  # noqa: ARG001
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    result: dict[str, Any] = async_redact_data(entry.as_dict(), TO_REDACT)
    return result
