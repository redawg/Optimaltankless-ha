"""Shared entity base for Optimal Tankless."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OptimalTanklessCoordinator


class OptimalTanklessEntity(CoordinatorEntity[OptimalTanklessCoordinator]):
    """Base entity for a single Optimal Tankless water heater."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OptimalTanklessCoordinator,
        description_key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._description_key = description_key
        device = coordinator.data
        serial = coordinator.device_id
        self._attr_unique_id = f"{serial}_{description_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=coordinator.entry.data.get("device_name")
            or device.get("name")
            or f"Opti {serial}",
            manufacturer="Its Optimal LLC",
            model=device.get("model"),
            sw_version=device.get("firmware_version"),
        )
