"""Cloud API client for Optimal Tankless (Opti+).

Uses the Optimal Hardware Backend at https://hwbe.itsoptimal.com

The /client/device/{serial}/... endpoints are currently reachable without login,
which allows Home Assistant setup with only the heater serial number.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL, VACATION_MODE_CONFIG_BIT

_LOGGER = logging.getLogger(__name__)

# Raw flowRate values appear to be milli-GPM (604 -> ~0.604 GPM).
FLOW_RATE_SCALE = 1000
# Raw heaterPower values appear to be watts (12000 -> 12 kW).
POWER_SCALE = 1000


class OptimalTanklessError(Exception):
    """Base exception for API errors."""


class OptimalTanklessAuthError(OptimalTanklessError):
    """Authentication failed."""


class OptimalTanklessConnectionError(OptimalTanklessError):
    """Network or server error."""


class OptimalTanklessAPI:
    """Async client for the Optimal HWBE API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the client."""
        self._session = session

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Optimaltankless-HA/0.2.0",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Perform an HTTP request against the Optimal HWBE API."""
        url = f"{API_BASE_URL}{path}"
        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 204:
                    return None
                body = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise OptimalTanklessConnectionError(str(err)) from err

        if response.status >= 400:
            raise OptimalTanklessConnectionError(f"HTTP {response.status}: {body}")

        return body

    async def async_get_device_status(self, serial_number: str | int) -> dict[str, Any]:
        """Fetch live telemetry and command state for one device."""
        serial = str(serial_number)
        snapshot = await self._request("GET", f"/client/device/{serial}/snapshots")
        if not isinstance(snapshot, dict):
            raise OptimalTanklessConnectionError("Unexpected snapshot response")

        command: dict[str, Any] | None = None
        try:
            cmd = await self._request("GET", f"/client/device/{serial}/commands")
            command = cmd if isinstance(cmd, dict) else None
        except OptimalTanklessConnectionError:
            _LOGGER.debug("Device command endpoint unavailable for %s", serial)

        return self._normalize_status(snapshot, command, serial)

    async def async_get_device_command(self, serial_number: str | int) -> dict[str, Any]:
        """Return the latest pending device command."""
        data = await self._request("GET", f"/client/device/{serial_number}/commands")
        if not isinstance(data, dict):
            raise OptimalTanklessConnectionError("Unexpected command response")
        return data

    async def async_set_command(
        self,
        serial_number: str | int,
        *,
        target_temperature: float,
        config_data: int,
        voltage_scale: float,
    ) -> None:
        """Push a device command (temperature and config flags)."""
        await self._request(
            "POST",
            f"/client/device/{serial_number}/commands",
            json={
                "targetTemperature": target_temperature,
                "configData": config_data,
                "voltageScale": voltage_scale,
            },
        )

    async def async_set_temperature(
        self, serial_number: str | int, temperature_f: float
    ) -> None:
        """Set target output temperature in Fahrenheit."""
        command = await self.async_get_device_command(serial_number)
        await self.async_set_command(
            serial_number,
            target_temperature=temperature_f,
            config_data=int(command.get("configData", 0)),
            voltage_scale=float(command.get("voltageScale", 1)),
        )

    async def async_set_vacation_mode(
        self, serial_number: str | int, enabled: bool
    ) -> None:
        """Enable or disable vacation mode via configData bit flag."""
        command = await self.async_get_device_command(serial_number)
        config_data = int(command.get("configData", 0))
        if enabled:
            config_data |= VACATION_MODE_CONFIG_BIT
        else:
            config_data &= ~VACATION_MODE_CONFIG_BIT

        await self.async_set_command(
            serial_number,
            target_temperature=float(command.get("targetTemperature", 120)),
            config_data=config_data,
            voltage_scale=float(command.get("voltageScale", 1)),
        )

    @staticmethod
    def _scale(value: Any, divisor: int) -> float | None:
        if value is None:
            return None
        return float(value) / divisor

    def _normalize_status(
        self,
        snapshot: dict[str, Any],
        command: dict[str, Any] | None,
        serial_number: str,
    ) -> dict[str, Any]:
        """Normalize HWBE JSON into stable keys for entities."""
        config_data = 0
        target_temperature = snapshot.get("targetTemp")
        voltage_scale = snapshot.get("voltageScale")

        if command:
            config_data = int(command.get("configData", 0))
            target_temperature = command.get("targetTemperature", target_temperature)
            voltage_scale = command.get("voltageScale", voltage_scale)

        heater_power = snapshot.get("heaterPower") or 0

        return {
            "serial_number": serial_number,
            "name": f"Opti {serial_number}",
            "model": snapshot.get("modelCode"),
            "firmware_version": str(snapshot.get("wifiFwVersion"))
            if snapshot.get("wifiFwVersion") is not None
            else None,
            "online": True,
            "heating": float(heater_power) > 0,
            "target_temperature": target_temperature,
            "outlet_temperature": snapshot.get("outputTemp"),
            "inlet_temperature": snapshot.get("inputTemp"),
            "flow_rate_gpm": self._scale(snapshot.get("flowRate"), FLOW_RATE_SCALE),
            "power_w": float(heater_power or 0),
            "power_kw": self._scale(heater_power, POWER_SCALE),
            "input_voltage": snapshot.get("acVoltage"),
            "heater_capacity": snapshot.get("heatCapacity"),
            "available_flow_rate": self._scale(
                snapshot.get("flowCapacity"), FLOW_RATE_SCALE
            ),
            "vacation_mode": False,
            "error_code": snapshot.get("error")
            or snapshot.get("heaterError")
            or snapshot.get("sensorError"),
            "config_data": config_data,
            "voltage_scale": voltage_scale,
        }
