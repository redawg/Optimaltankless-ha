"""Water heater platform for Optimal Tankless."""

from __future__ import annotations

from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import MAX_TEMP_F, MIN_TEMP_F, clamp_temperature_f
from .coordinator import OptimalTanklessCoordinator
from .entity import OptimalTanklessEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up water heater entities."""
    coordinator: OptimalTanklessCoordinator = entry.runtime_data
    async_add_entities([OptimalTanklessWaterHeater(coordinator)])


class OptimalTanklessWaterHeater(OptimalTanklessEntity, WaterHeaterEntity):
    """Representation of an Optimal Tankless water heater."""

    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_supported_features = WaterHeaterEntityFeature.TARGET_TEMPERATURE
    _attr_min_temp = MIN_TEMP_F
    _attr_max_temp = MAX_TEMP_F

    def __init__(self, coordinator: OptimalTanklessCoordinator) -> None:
        """Initialize the water heater."""
        super().__init__(coordinator, "water_heater")
        self._attr_name = None

    @property
    def current_operation(self) -> str:
        """Return current operation."""
        if self.coordinator.data.get("heating"):
            return "heat_pump"  # closest HA operation for active heating
        return "idle"

    @property
    def operation_list(self) -> list[str]:
        """Return supported operations."""
        return ["idle", "heat_pump"]

    @property
    def current_temperature(self) -> float | None:
        """Return current outlet temperature."""
        return self.coordinator.data.get("outlet_temperature")

    @property
    def target_temperature(self) -> float | None:
        """Return target setpoint clamped to the heater's supported range."""
        return clamp_temperature_f(self.coordinator.data.get("target_temperature"))

    @property
    def is_away_mode_on(self) -> bool | None:
        """Vacation/away mode is not exposed until configData bits are mapped."""
        return None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return
        temperature = clamp_temperature_f(float(temperature))
        if temperature is None:
            return
        await self.coordinator.api.async_set_temperature(
            self.coordinator.device_id, temperature
        )
        await self.coordinator.async_request_refresh()
