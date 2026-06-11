"""Binary sensor platform for Optimal Tankless."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import OptimalTanklessCoordinator
from .entity import OptimalTanklessEntity


@dataclass(frozen=True, kw_only=True)
class OptimalTanklessBinarySensorDescription(BinarySensorEntityDescription):
    """Describe an Optimal Tankless binary sensor."""

    data_key: str


BINARY_SENSORS: tuple[OptimalTanklessBinarySensorDescription, ...] = (
    OptimalTanklessBinarySensorDescription(
        key="heating",
        data_key="heating",
        translation_key="heating",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    OptimalTanklessBinarySensorDescription(
        key="online",
        data_key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    coordinator: OptimalTanklessCoordinator = entry.runtime_data
    async_add_entities(
        OptimalTanklessBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class OptimalTanklessBinarySensor(OptimalTanklessEntity, BinarySensorEntity):
    """Optimal Tankless binary sensor."""

    entity_description: OptimalTanklessBinarySensorDescription

    def __init__(
        self,
        coordinator: OptimalTanklessCoordinator,
        description: OptimalTanklessBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        self.entity_description = description
        super().__init__(coordinator, description.key)

    @property
    def is_on(self) -> bool | None:
        """Return sensor state."""
        value = self.coordinator.data.get(self.entity_description.data_key)
        return bool(value) if value is not None else None
