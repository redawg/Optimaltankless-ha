"""Config flow for Optimal Tankless."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OptimalTanklessAPI, OptimalTanklessConnectionError
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SERIAL_NUMBER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_SCHEMA = vol.All(
    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
)

SETUP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERIAL_NUMBER): str,
        vol.Optional("device_name"): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): SCAN_INTERVAL_SCHEMA,
    }
)


class OptimalTanklessConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Optimal Tankless."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure using the heater serial number only."""
        errors: dict[str, str] = {}

        if user_input is not None:
            serial = user_input[CONF_SERIAL_NUMBER].strip().lstrip("#")
            if not serial.isdigit():
                errors[CONF_SERIAL_NUMBER] = "invalid_serial"
            else:
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured()

                session = async_get_clientsession(self.hass)
                api = OptimalTanklessAPI(session)
                try:
                    await api.async_get_device_status(serial)
                except OptimalTanklessConnectionError as err:
                    _LOGGER.debug("Device validation failed: %s", err)
                    errors[CONF_SERIAL_NUMBER] = "device_not_found"
                else:
                    name = user_input.get("device_name") or f"Opti {serial}"
                    scan_interval = user_input.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    )
                    return self.async_create_entry(
                        title=f"{name} ({serial})",
                        data={
                            CONF_SERIAL_NUMBER: serial,
                            "device_name": name,
                        },
                        options={CONF_SCAN_INTERVAL: scan_interval},
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=SETUP_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        """Return options flow handler."""
        return OptimalTanklessOptionsFlowHandler(config_entry)


class OptimalTanklessOptionsFlowHandler(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): SCAN_INTERVAL_SCHEMA,
                }
            ),
        )
