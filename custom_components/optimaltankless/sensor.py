"""Sensor platform for Optimal Tankless."""

from __future__ import annotations

import time
from dataclasses import dataclass

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_AVAILABLE_FLOW,
    ATTR_ERROR_CODE,
    ATTR_FLOW_RATE,
    ATTR_HEATER_CAPACITY,
    ATTR_INLET_TEMP,
    ATTR_INPUT_VOLTAGE,
    ATTR_OUTLET_TEMP,
    ATTR_POWER_W,
)
from .coordinator import OptimalTanklessCoordinator
from .entity import OptimalTanklessEntity


@dataclass(frozen=True, kw_only=True)
class OptimalTanklessSensorDescription(SensorEntityDescription):
    """Describe an Optimal Tankless sensor."""

    data_key: str


SENSORS: tuple[OptimalTanklessSensorDescription, ...] = (
    OptimalTanklessSensorDescription(
        key="inlet_temperature",
        data_key=ATTR_INLET_TEMP,
        translation_key="inlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    OptimalTanklessSensorDescription(
        key="outlet_temperature",
        data_key=ATTR_OUTLET_TEMP,
        translation_key="outlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
    ),
    OptimalTanklessSensorDescription(
        key="flow_rate",
        data_key=ATTR_FLOW_RATE,
        translation_key="flow_rate",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumeFlowRate.GALLONS_PER_MINUTE,
    ),
    OptimalTanklessSensorDescription(
        key="power",
        data_key=ATTR_POWER_W,
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
    ),
    OptimalTanklessSensorDescription(
        key="input_voltage",
        data_key=ATTR_INPUT_VOLTAGE,
        translation_key="input_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    OptimalTanklessSensorDescription(
        key="heater_capacity",
        data_key=ATTR_HEATER_CAPACITY,
        translation_key="heater_capacity",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    OptimalTanklessSensorDescription(
        key="available_flow_rate",
        data_key=ATTR_AVAILABLE_FLOW,
        translation_key="available_flow_rate",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumeFlowRate.GALLONS_PER_MINUTE,
    ),
    OptimalTanklessSensorDescription(
        key="error_code",
        data_key=ATTR_ERROR_CODE,
        translation_key="error_code",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator: OptimalTanklessCoordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        OptimalTanklessSensor(coordinator, description) for description in SENSORS
    ]
    entities.append(OptimalTanklessEnergySensor(coordinator))
    async_add_entities(entities)


class OptimalTanklessSensor(OptimalTanklessEntity, SensorEntity):
    """Optimal Tankless sensor."""

    entity_description: OptimalTanklessSensorDescription

    def __init__(
        self,
        coordinator: OptimalTanklessCoordinator,
        description: OptimalTanklessSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        super().__init__(coordinator, description.key)

    @property
    def native_value(self) -> str | float | None:
        """Return sensor value."""
        return self.coordinator.data.get(self.entity_description.data_key)


class OptimalTanklessEnergySensor(OptimalTanklessEntity, RestoreSensor, SensorEntity):
    """Integrate heater power readings into cumulative energy use."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_translation_key = "energy_consumption"

    def __init__(self, coordinator: OptimalTanklessCoordinator) -> None:
        """Initialize the energy sensor."""
        super().__init__(coordinator, "energy_consumption")
        self._energy_kwh = 0.0
        self._last_power_w: float | None = None
        self._last_update: float | None = None

    async def async_added_to_hass(self) -> None:
        """Restore cumulative energy after restart."""
        await super().async_added_to_hass()
        if (last_sensor_data := await self.async_get_last_sensor_data()) is not None:
            try:
                self._energy_kwh = float(last_sensor_data.native_value or 0)
            except (TypeError, ValueError):
                self._energy_kwh = 0.0

    @property
    def native_value(self) -> float:
        """Return cumulative energy consumption in kWh."""
        return round(self._energy_kwh, 3)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Integrate power between cloud polls."""
        now = time.time()
        power_w = float(self.coordinator.data.get(ATTR_POWER_W) or 0)

        if self._last_update is not None:
            dt_hours = (now - self._last_update) / 3600
            if self._last_power_w is None:
                avg_w = power_w
            else:
                avg_w = (self._last_power_w + power_w) / 2
            self._energy_kwh += (avg_w / 1000) * dt_hours

        self._last_update = now
        self._last_power_w = power_w
        super()._handle_coordinator_update()
