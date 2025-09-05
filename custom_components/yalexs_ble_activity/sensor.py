"""Support for Yale Access Bluetooth Activity sensors."""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from homeassistant.components import recorder
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.yalexs_ble.entity import YALEXSBLEEntity
from homeassistant.components.yalexs_ble.models import YaleXSBLEData
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers import entity_registry as er, event as evt
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import (
    ExtraStoredData,
    RestoredExtraData,
    RestoreEntity,
)
from homeassistant.util import dt as dt_util
from yalexs_ble import ConnectionInfo, DoorActivity, LockActivity, LockInfo

from .const import (
    ATTR_REMOTE_TYPE,
    ATTR_SLOT,
    ATTR_SOURCE,
    ATTR_TIMESTAMP,
    CONF_LOCK_ENTITIES,
    OPERATION_SENSOR_WRITE_DELAY,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(  # noqa: RUF029
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Yale Access Bluetooth Activity sensors."""

    entity_registry = er.async_get(hass)

    async_add_entities(
        YaleXSBLEOperationSensor(data)
        for lock_enitity_id in entry.data[CONF_LOCK_ENTITIES]
        if (
            (lock_entry := entity_registry.async_get(lock_enitity_id))
            and (core_entry_id := lock_entry.config_entry_id)
            and (core_entry := hass.config_entries.async_get_known_entry(core_entry_id))
            and (data := core_entry.runtime_data)
        )
    )


class YaleXSBLEOperationSensor(YALEXSBLEEntity, SensorEntity, RestoreEntity):
    """Representation of an Yale Access Bluetooth lock operation sensor."""

    _attr_translation_key = "operation"
    _attr_icon = "mdi:lock-clock"
    _pending_activity_update: DoorActivity | LockActivity | None = None
    _cancel_pending_activity_update: CALLBACK_TYPE | None = None

    def __init__(
        self,
        data: YaleXSBLEData,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(data)
        self._attr_unique_id = f"{data.lock.address}operation"

    @callback
    def _async_activity_update(
        self,
        activity: DoorActivity | LockActivity,
        lock_info: LockInfo,  # noqa: ARG002
        connection_info: ConnectionInfo,  # noqa: ARG002
    ) -> None:
        """Handle activity update."""

        value, attributes = self._extract_values(activity)

        _LOGGER.debug("creating event for activity update")

        self.hass.bus.async_fire(
            "yalexs_ble_activity",
            {
                "entity_id": self.entity_id,
                "state": value,
                "attributes": attributes,
            },
        )

        if self._pending_activity_update:
            self._record_pending_update()

        self._pending_activity_update = activity

        if self._cancel_pending_activity_update:
            self._cancel_pending_activity_update()

        self._cancel_pending_activity_update = evt.async_call_later(
            self.hass,
            OPERATION_SENSOR_WRITE_DELAY,
            self._flush_pending_update,
        )

    def _record_pending_update(self) -> None:
        activity = self._pending_activity_update
        assert activity is not None
        native_value, attributes = self._extract_values(activity)
        state_changed_data: EventStateChangedData = {
            "entity_id": self.entity_id,
            "old_state": None,
            "new_state": State(
                self.entity_id,
                native_value or STATE_UNAVAILABLE,
                attributes,
                last_changed=activity.timestamp,
                last_reported=activity.timestamp,
                last_updated=activity.timestamp,
                last_updated_timestamp=dt_util.as_timestamp(activity.timestamp),
            ),
        }

        _LOGGER.debug("writing historic activity update: %s", state_changed_data)

        instance = recorder.get_instance(self.hass)
        instance.queue_task(Event(str(EVENT_STATE_CHANGED), state_changed_data))

    @callback
    def _flush_pending_update(self, now: dt.datetime) -> None:  # noqa: ARG002
        activity = self._pending_activity_update
        assert activity is not None

        _LOGGER.debug("flushing pending activity update")

        self._attr_native_value, self._attr_extra_state_attributes = (
            self._extract_values(activity)
        )
        self._pending_activity_update = None

        self.async_write_ha_state()

    @staticmethod
    def _extract_values(
        activity: DoorActivity | LockActivity,
    ) -> tuple[str | None, dict[str, Any]]:
        value: str | None = None
        attributes: dict[str, Any] = {}

        if isinstance(activity, DoorActivity):
            value = f"door_{activity.status.name.lower()}"
            attributes[ATTR_TIMESTAMP] = activity.timestamp
        elif isinstance(activity, LockActivity):
            value = f"lock_{activity.status.name.lower()}"
            attributes[ATTR_TIMESTAMP] = activity.timestamp
            attributes[ATTR_SOURCE] = activity.source.name.lower()
            if activity.remote_type is not None:
                attributes[ATTR_REMOTE_TYPE] = activity.remote_type.name.lower()
            if activity.slot is not None:
                attributes[ATTR_SLOT] = activity.slot

        return (value, attributes)

    async def async_added_to_hass(self) -> None:
        """Register callbacks, perform initial updates & restore state."""
        await super().async_added_to_hass()

        self.async_on_remove(
            self._device.register_activity_callback(
                self._async_activity_update, request_update=True
            )
        )

        if (
            (last_state := await self.async_get_last_state()) is not None
            and last_state.state not in {STATE_UNKNOWN, STATE_UNAVAILABLE}
            and (extra_data := await self.async_get_last_extra_data()) is not None
        ):
            extra_data_dict = extra_data.as_dict()
            self._attr_native_value = extra_data_dict["value"]
            self._attr_extra_state_attributes = extra_data_dict["attributes"]

    @property
    def extra_restore_state_data(self) -> ExtraStoredData | None:
        return RestoredExtraData(
            {
                "value": self._attr_native_value,
                "attributes": self._attr_extra_state_attributes,
            }
        )
