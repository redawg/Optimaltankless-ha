"""DataUpdateCoordinator for Optimal Tankless devices."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OptimalTanklessAPI, OptimalTanklessAuthError, OptimalTanklessConnectionError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, entry_options

_LOGGER = logging.getLogger(__name__)


class OptimalTanklessCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch and cache state for one water heater."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: OptimalTanklessAPI,
        device_id: str,
    ) -> None:
        """Initialize."""
        self.entry = entry
        self.api = api
        self.device_id = device_id
        scan_interval = entry_options(entry).get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device_id}",
            update_interval=timedelta(seconds=scan_interval),
        )

    def set_scan_interval(self, scan_interval: int) -> None:
        """Apply a new polling interval without reloading the integration."""
        self.update_interval = timedelta(seconds=scan_interval)
        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None
        if not self.disabled:
            self._schedule_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll cloud API for the latest device state."""
        try:
            return await self.api.async_get_device_status(self.device_id)
        except OptimalTanklessAuthError as err:
            raise UpdateFailed("Authentication failed") from err
        except OptimalTanklessConnectionError as err:
            raise UpdateFailed("Unable to reach Optimal cloud") from err
