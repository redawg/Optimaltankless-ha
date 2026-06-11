"""The Optimal Tankless integration."""

from __future__ import annotations

import logging

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OptimalTanklessAPI, OptimalTanklessConnectionError
from .const import CONF_SERIAL_NUMBER, DOMAIN
from .coordinator import OptimalTanklessCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.WATER_HEATER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]

if TYPE_CHECKING:
    OptimalTanklessConfigEntry = ConfigEntry[OptimalTanklessCoordinator]
else:
    OptimalTanklessConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: OptimalTanklessConfigEntry) -> bool:
    """Set up Optimal Tankless from a config entry."""
    session = async_get_clientsession(hass)
    api = OptimalTanklessAPI(session)

    try:
        await api.async_get_device_status(entry.data[CONF_SERIAL_NUMBER])
    except OptimalTanklessConnectionError as err:
        raise ConfigEntryNotReady("Unable to connect to Optimal cloud") from err

    coordinator = OptimalTanklessCoordinator(
        hass,
        entry,
        api,
        entry.data[CONF_SERIAL_NUMBER],
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: OptimalTanklessConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry.runtime_data = None
    return unload_ok
