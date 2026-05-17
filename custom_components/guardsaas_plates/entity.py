"""Base entity for GuardSaaS Plates."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import GuardSaaSPlatesCoordinator


class GuardSaaSPlatesEntity(CoordinatorEntity[GuardSaaSPlatesCoordinator]):
    """Base GuardSaaS Plates entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GuardSaaSPlatesCoordinator) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=DEFAULT_NAME,
            manufacturer="GuardSaaS",
            model="Employee export",
        )
