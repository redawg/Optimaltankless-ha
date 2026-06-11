"""The Optimal Tankless integration."""

from __future__ import annotations

import logging

from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OptimalTanklessAPI, OptimalTanklessConnectionError
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_NUMBER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    SERVICE_SET_SCAN_INTERVAL,
    entry_options,
)
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

SET_SCAN_INTERVAL_SCHEMA = vol.Schema(
    {
        vol.Optional("config_entry_id"): str,
        vol.Required(CONF_SCAN_INTERVAL): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
        ),
    }
)


def _scan_interval_from_entry(entry: ConfigEntry) -> int:
    """Return the configured polling interval for a config entry."""
    return int(
        entry_options(entry).get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )


async def _async_update_listener(
    hass: HomeAssistant, entry: OptimalTanklessConfigEntry
) -> None:
    """Apply option changes without reloading entities."""
    coordinator = entry.runtime_data
    if coordinator is None:
        return
    coordinator.set_scan_interval(_scan_interval_from_entry(entry))


async def _async_set_scan_interval(hass: HomeAssistant, call: ServiceCall) -> None:
    """Update polling interval for one or all Optimal Tankless entries."""
    scan_interval = int(call.data[CONF_SCAN_INTERVAL])
    target_entry_id = call.data.get("config_entry_id")

    entries = hass.config_entries.async_entries(DOMAIN)
    if target_entry_id:
        entries = [entry for entry in entries if entry.entry_id == target_entry_id]

    if not entries:
        raise ServiceValidationError("No Optimal Tankless config entries matched")

    for entry in entries:
        hass.config_entries.async_update_entry(
            entry,
            options={
                **entry_options(entry),
                CONF_SCAN_INTERVAL: scan_interval,
            },
        )


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

    if not hass.services.has_service(DOMAIN, SERVICE_SET_SCAN_INTERVAL):

        async def async_set_scan_interval(call: ServiceCall) -> None:
            await _async_set_scan_interval(hass, call)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_SCAN_INTERVAL,
            async_set_scan_interval,
            schema=SET_SCAN_INTERVAL_SCHEMA,
        )

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: OptimalTanklessConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry.runtime_data = None

    if unload_ok and not hass.config_entries.async_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_SET_SCAN_INTERVAL)

    return unload_ok
