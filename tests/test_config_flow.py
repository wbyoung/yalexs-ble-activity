"""Test Yale Access Bluetooth Activity config flow."""

from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.yalexs_ble_activity.const import CONF_LOCK_ENTITIES, DOMAIN


@pytest.mark.parametrize(
    ("user_input", "expected_result"),
    [
        (
            {
                CONF_LOCK_ENTITIES: ["lock.front_door"],
            },
            {
                CONF_LOCK_ENTITIES: ["lock.front_door"],
            },
        ),
    ],
)
async def test_user_flow(
    hass: HomeAssistant,
    lock: er.RegistryEntry,
    user_input: dict,
    expected_result: dict,
) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.yalexs_ble_activity.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"] == expected_result

        assert result["title"] == "Yale Access Bluetooth Activity"

        await hass.async_block_till_done()

    assert mock_setup_entry.called


async def test_options_flow(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test options flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        title="home",
        data={
            CONF_LOCK_ENTITIES: ["lock.front_door"],
        },
    )
    mock_config.add_to_hass(hass)

    with patch(
        "custom_components.yalexs_ble_activity.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        await hass.config_entries.async_setup(mock_config.entry_id)
        await hass.async_block_till_done()
        assert mock_setup_entry.called

        result = await hass.config_entries.options.async_init(mock_config.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_LOCK_ENTITIES: ["lock.front_door"],
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config.data == {
        CONF_LOCK_ENTITIES: ["lock.front_door"],
    }
