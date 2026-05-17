"""Sensors for GuardSaaS Plates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GuardSaaSPlatesCoordinator
from .entity import GuardSaaSPlatesEntity


def _parse_timestamp(value: Any) -> datetime | None:
    """Return timezone-aware datetime for Home Assistant timestamp sensors."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    if not isinstance(value, str) or not value.strip():
        return None

    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


@dataclass(frozen=True, kw_only=True)
class GuardSaaSPlatesSensorDescription(SensorEntityDescription):
    """GuardSaaS Plates sensor description."""

    value_fn: Callable[[dict[str, Any]], Any]
    suggested_object_id: str | None = None
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSORS: tuple[GuardSaaSPlatesSensorDescription, ...] = (
    GuardSaaSPlatesSensorDescription(
        key="allowed_plates",
        translation_key="allowed_plates",
        icon="mdi:phone-check",
        suggested_object_id="guardsaas_plates_allowed_plates",
        value_fn=lambda data: data.get("state"),
        attrs_fn=lambda data: {
            "count": data.get("count", 0),
            "content": data.get("content", ""),
            "plates_data": data.get("plates_data", {}),
            "timestamp": data.get("timestamp"),
            "status": data.get("status"),
            "from_cache": data.get("from_cache"),
            "error": data.get("error"),
        },
    ),
    GuardSaaSPlatesSensorDescription(
        key="plates_count",
        translation_key="plates_count",
        icon="mdi:barcode-scan",
        suggested_object_id="guardsaas_plates_count",
        value_fn=lambda data: data.get("count", 0),
    ),
    GuardSaaSPlatesSensorDescription(
        key="last_update",
        translation_key="last_update",
        icon="mdi:update",
        suggested_object_id="guardsaas_plates_last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _parse_timestamp(data.get("timestamp")),
        attrs_fn=lambda data: {
            "status": data.get("status"),
            "from_cache": data.get("from_cache"),
            "error": data.get("error"),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator: GuardSaaSPlatesCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(GuardSaaSPlatesSensor(coordinator, description) for description in SENSORS)


class GuardSaaSPlatesSensor(GuardSaaSPlatesEntity, SensorEntity):
    """GuardSaaS Plates sensor."""

    entity_description: GuardSaaSPlatesSensorDescription

    def __init__(
        self,
        coordinator: GuardSaaSPlatesCoordinator,
        description: GuardSaaSPlatesSensorDescription,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_suggested_object_id = description.suggested_object_id

    @property
    def native_value(self) -> Any:
        """Return native value."""
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes."""
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data or {})
