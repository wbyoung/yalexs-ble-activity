"""Fixtures for testing."""

from collections.abc import Generator
import logging
from unittest.mock import AsyncMock, Mock, patch

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, mock_component

from custom_components.yalexs_ble_activity.const import (
    CONF_LOCK_ENTITIES,
    DOMAIN,
    TRACE,
)

from . import MOCK_UTC_NOW, MockNow, add_mock_lock, setup_integration

_LOGGER = logging.getLogger(__name__)


def pytest_configure(config) -> None:
    is_capturing = config.getoption("capture") != "no"

    if not is_capturing and config.pluginmanager.hasplugin("logging"):
        _LOGGER.warning(
            "pytest run with `-s/--capture=no` and the logging plugin enabled "
            "run with `-p no:logging` to disable all sources of log capturing.",
        )

    # `pytest_homeassistant_custom_component` calls `logging.basicConfig` which
    # creates the `stderr` stream handler. in most cases that will result in
    # logs being duplicated, reported in the "stderr" and "logging" capture
    # sections. force reconfiguration, removing handlers when not running with
    # the `-s/--capture=no` flag.
    if is_capturing:
        logging.basicConfig(level=logging.INFO, handlers=[], force=True)

    logging.getLogger("custom_components.yalexs_ble_activity").setLevel(TRACE)
    logging.getLogger("homeassistant").setLevel(logging.INFO)
    logging.getLogger("pytest_homeassistant_custom_component").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.ERROR)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return


@pytest.fixture(autouse=True)
def mock_dependencies(hass: HomeAssistant) -> None:
    """Mock dependencies loaded."""
    mock_component(hass, "yalexs_ble")


@pytest.fixture(autouse=True)
def mock_recorder(
    enable_custom_integrations,
) -> Generator[None]:
    """Mock recorder."""

    with patch(
        "homeassistant.components.recorder.get_instance",
    ):
        yield


@pytest.fixture(autouse=True)
def mock_yalexs_ble(
    enable_custom_integrations,
) -> Generator[dict[str, Mock | AsyncMock]]:
    """Mock internals of Yale Access Bluetooth integration."""

    with (
        patch(
            "homeassistant.components.yalexs_ble.entity.YALEXSBLEEntity.async_added_to_hass",
        ) as mock_async_added_to_hass,
    ):
        yield {
            "async_added_to_hass": mock_async_added_to_hass,
        }


@pytest.fixture(name="now")
def mock_now(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
) -> MockNow:
    """Return a mock now & utcnow datetime."""
    freezer.move_to(MOCK_UTC_NOW)

    return MockNow(hass, freezer)


@pytest.fixture(name="config_entry")
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Yale Access Bluetooth Activity",
        entry_id="mock-entry-id",
        data={
            CONF_LOCK_ENTITIES: ["lock.front_door"],
        },
    )


@pytest.fixture(name="lock")
def mock_lock(
    hass: HomeAssistant,
) -> er.RegistryEntry:
    """Return the default mocked config entry."""

    return add_mock_lock(
        hass,
        "lock.front_door",
        {"manufacturer": "Yale"},
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> MockConfigEntry:
    """Set up the Yale Access Bluetooth Activity integration for testing."""
    await setup_integration(hass, config_entry)

    return config_entry
