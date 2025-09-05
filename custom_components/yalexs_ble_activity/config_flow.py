"""Config flow for Yale Access Bluetooth Activity integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import DOMAIN as LOCK_DOMAIN
from homeassistant.components.yalexs_ble.const import DOMAIN as YALEXSBLE_DOMAIN
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig
import voluptuous as vol

from .const import CONF_LOCK_ENTITIES, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_LOCK_ENTITIES,
        ): EntitySelector(
            EntitySelectorConfig(
                integration=YALEXSBLE_DOMAIN,
                domain=[LOCK_DOMAIN],
                multiple=True,
            ),
        ),
    }
)


class YaleXSBLEActivityConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a Yale Access Bluetooth Activity config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,  # noqa: ARG004
    ) -> OptionsFlow:
        """Get the options flow for this handler.

        Returns:
            The options flow.
        """
        return YaleXSBLEActivityOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user.

        Returns:
            The config flow result.
        """
        if user_input is not None:
            return self.async_create_entry(
                title="Yale Access Bluetooth Activity", data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
        )


class YaleXSBLEActivityOptionsFlow(OptionsFlow):
    """Handle a option flow."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle options flow.

        Returns:
            The config flow result.
        """
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
            )
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA,
                self.config_entry.data if user_input is None else user_input,
            ),
        )
