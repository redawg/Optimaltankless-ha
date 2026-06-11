"""Sensor platform for Optimal Tankless."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_AVAILABLE_FLOW,
    ATTR_ERROR_CODE,
    ATTR_FLOW_RATE,
    ATTR_HEATER_CAPACITY,
    ATTR_INLET_TEMP,
    ATTR_INPUT_VOLTAGE,
    ATTR_OUTLET_TEMP,
    ATTR_POWER_KW,
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
        data_key=ATTR_POWER_KW,
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
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
    async_add_entities(
        OptimalTanklessSensor(coordinator, description) for description in SENSORS
    )


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
