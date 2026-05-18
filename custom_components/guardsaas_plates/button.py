"""Buttons for GuardSaaS Plates."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Set up button."""
    coordinator: GuardSaaSPlatesCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GuardSaaSRefreshButton(coordinator)])


class GuardSaaSRefreshButton(GuardSaaSPlatesEntity, ButtonEntity):
    """Manual refresh button."""

    _attr_translation_key = "refresh_plates"
    _attr_icon = "mdi:update"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_suggested_object_id = "guardsaas_plates_refresh_plates"

    def __init__(self, coordinator: GuardSaaSPlatesCoordinator) -> None:
        """Initialize button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_refresh_plates"

    async def async_press(self) -> None:
        """Refresh GuardSaaS data."""
        await self.coordinator.async_request_refresh()
