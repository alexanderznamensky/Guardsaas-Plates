"""GuardSaaS Plates integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_UPDATE_INTERVAL_HOURS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
)
from .coordinator import GuardSaaSPlatesCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


def _get_update_interval_seconds(entry: ConfigEntry) -> int:
    """Return update interval in seconds.

    New versions store the value in hours. Older versions stored
    ``scan_interval`` in seconds, so keep reading it for existing entries.
    """
    if CONF_UPDATE_INTERVAL_HOURS in entry.options:
        return max(1, int(float(entry.options[CONF_UPDATE_INTERVAL_HOURS]) * 3600))
    if CONF_UPDATE_INTERVAL_HOURS in entry.data:
        return max(1, int(float(entry.data[CONF_UPDATE_INTERVAL_HOURS]) * 3600))
    if CONF_SCAN_INTERVAL in entry.options:
        return max(1, int(entry.options[CONF_SCAN_INTERVAL]))
    if CONF_SCAN_INTERVAL in entry.data:
        return max(1, int(entry.data[CONF_SCAN_INTERVAL]))
    return int(DEFAULT_SCAN_INTERVAL)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GuardSaaS Plates from a config entry."""
    update_interval_seconds = _get_update_interval_seconds(entry)

    coordinator = GuardSaaSPlatesCoordinator(
        hass=hass,
        entry=entry,
        update_interval=timedelta(seconds=update_interval_seconds),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
