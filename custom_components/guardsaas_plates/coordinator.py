"""Data coordinator for GuardSaaS Plates."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import GuardSaaSClient
from .const import (
    CONF_CACHE_FILE,
    CONF_MANDATORY_PLATES,
    CONF_PASSWORD,
    CONF_USERNAME,
    DEFAULT_CACHE_FILE,
    DEFAULT_MANDATORY_PLATES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class GuardSaaSPlatesCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """GuardSaaS Plates update coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        update_interval: timedelta,
    ) -> None:
        """Initialize coordinator."""
        self.entry = entry
        cache_file = entry.options.get(CONF_CACHE_FILE, entry.data.get(CONF_CACHE_FILE, DEFAULT_CACHE_FILE))
        if not str(cache_file).startswith("/"):
            cache_file = hass.config.path(str(cache_file))

        mandatory_plates = entry.options.get(
            CONF_MANDATORY_PLATES,
            entry.data.get(CONF_MANDATORY_PLATES, DEFAULT_MANDATORY_PLATES),
        )
        if isinstance(mandatory_plates, str):
            mandatory_plates = [p.strip() for p in mandatory_plates.split(",") if p.strip()]

        self.client = GuardSaaSClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            cache_file=str(cache_file),
            mandatory_plates=list(mandatory_plates),
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from GuardSaaS."""
        try:
            return await self.hass.async_add_executor_job(self.client.update)
        except Exception as exc:
            raise UpdateFailed(f"GuardSaaS update failed: {exc}") from exc
