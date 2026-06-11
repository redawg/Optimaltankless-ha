"""Switch platform for Optimal Tankless."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import OptimalTanklessCoordinator
from .entity import OptimalTanklessEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    coordinator: OptimalTanklessCoordinator = entry.runtime_data
    async_add_entities([OptimalTanklessVacationSwitch(coordinator)])


class OptimalTanklessVacationSwitch(OptimalTanklessEntity, SwitchEntity):
    """Vacation mode switch (mirrors water_heater away mode)."""

    _attr_translation_key = "vacation_mode"

    def __init__(self, coordinator: OptimalTanklessCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "vacation_mode")

    @property
    def is_on(self) -> bool | None:
        """Return whether vacation mode is enabled."""
        value = self.coordinator.data.get("vacation_mode")
        return bool(value) if value is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable vacation mode."""
        await self.coordinator.api.async_set_vacation_mode(
            self.coordinator.device_id, True
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable vacation mode."""
        await self.coordinator.api.async_set_vacation_mode(
            self.coordinator.device_id, False
        )
        await self.coordinator.async_request_refresh()
