"""Binary sensors for GuardSaaS Plates."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GuardSaaSPlatesCoordinator
from .entity import GuardSaaSPlatesEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator: GuardSaaSPlatesCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GuardSaaSAuthBinarySensor(coordinator)])


class GuardSaaSAuthBinarySensor(GuardSaaSPlatesEntity, BinarySensorEntity):
    """GuardSaaS authentication status."""

    _attr_translation_key = "auth_status"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: GuardSaaSPlatesCoordinator) -> None:
        """Initialize binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_auth_status"
        self._attr_suggested_object_id = "guardsaas_plates_auth_status"

    @property
    def is_on(self) -> bool:
        """Return True if last authentication was successful."""
        return bool((self.coordinator.data or {}).get("authenticated"))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return extra attributes."""
        data = self.coordinator.data or {}
        return {
            "from_cache": data.get("from_cache"),
            "error": data.get("error"),
            "timestamp": data.get("timestamp"),
        }
