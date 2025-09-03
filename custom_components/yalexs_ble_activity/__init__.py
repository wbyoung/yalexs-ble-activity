"""The Yale Access Bluetooth Activity integration."""

from __future__ import annotations

from functools import partial
from importlib.metadata import version
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.event import async_track_entity_registry_updated_event
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.util import package as pkg_util
import yalexs_ble

from .const import CONF_LOCK_ENTITIES, DOMAIN, YALEXSBLE_PATCH_URL

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
YALEXSBLE_VERSION = version("yalexs-ble")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Yale Access Bluetooth Activity from a config entry.

    Returns:
        If the setup was successful.

    Raises:
        ConfigEntryError: If there is an issue with setup.
    """
    _LOGGER.debug("setup %s with config:%s", entry.title, entry.data)

    if not hasattr(yalexs_ble.PushLock, "register_activity_callback"):
        _LOGGER.debug("%s no activity callback:%s", entry.title, entry.data)

        def _install_yalexs_ble_patch() -> bool:
            return bool(
                pkg_util.install_package(
                    YALEXSBLE_PATCH_URL.format(version=YALEXSBLE_VERSION)
                )
            )

        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="yalexs_ble_patched"
            if (await hass.async_add_executor_job(_install_yalexs_ble_patch))
            else "yalexs_ble_no_patch_available",
            translation_placeholders={
                "yalexs_ble_version": YALEXSBLE_VERSION,
            },
        )

    entry.async_on_unload(
        async_track_entity_registry_updated_event(
            hass,
            entry.data[CONF_LOCK_ENTITIES],
            partial(_async_handle_lock_entity_change, hass, entry),
        ),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_handle_lock_entity_change(  # noqa: RUF029
    hass: HomeAssistant,
    entry: ConfigEntry,
    event: Event[er.EventEntityRegistryUpdatedData],
) -> None:
    """Fetch and process tracked entity change event."""
    data = event.data
    lock_entity_ids: list[str] = entry.data[CONF_LOCK_ENTITIES]

    if data["action"] == "remove":
        _create_removed_lock_entity_issue(hass, data["entity_id"])

    if data["action"] == "update" and "entity_id" in data["changes"]:
        old_lock_id = data["old_entity_id"]
        new_lock_id = data["entity_id"]

        hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_LOCK_ENTITIES: [
                    new_lock_id if lock_id == old_lock_id else lock_id
                    for lock_id in lock_entity_ids
                ],
            },
        )


def _create_removed_lock_entity_issue(
    hass: HomeAssistant,
    entity_id: str,
) -> None:
    """Create a repair issue for a removed lock entity."""
    async_create_issue(
        hass,
        DOMAIN,
        f"lock_entity_removed_{entity_id}",
        is_fixable=True,
        is_persistent=True,
        severity=IssueSeverity.WARNING,
        translation_key="lock_entity_removed",
        translation_placeholders={
            "entity_id": entity_id,
        },
    )
