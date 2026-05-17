"""Config flow for GuardSaaS Plates."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .client import GuardSaaSClient
from .const import (
    CONF_CACHE_FILE,
    CONF_MANDATORY_PLATES,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_UPDATE_INTERVAL_HOURS,
    CONF_USERNAME,
    DEFAULT_CACHE_FILE,
    DEFAULT_MANDATORY_PLATES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
)


def _plates_to_string(value: Any) -> str:
    """Convert plates list/string to comma separated string."""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, str):
        return value
    return ""


def _plates_from_string(value: str) -> list[str]:
    """Convert comma/newline separated string to list."""
    return [item.strip().upper() for item in value.replace("\n", ",").split(",") if item.strip()]


def _hours_from_entry_value(value: Any) -> float:
    """Return hours from stored value."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(DEFAULT_UPDATE_INTERVAL_HOURS)


def _legacy_seconds_to_hours(value: Any) -> float:
    """Convert legacy seconds value to hours for the options UI."""
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return float(DEFAULT_UPDATE_INTERVAL_HOURS)
    if seconds <= 0:
        return float(DEFAULT_UPDATE_INTERVAL_HOURS)
    return round(seconds / 3600, 3)


class GuardSaaSPlatesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GuardSaaS Plates."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mandatory_plates = _plates_from_string(user_input.get(CONF_MANDATORY_PLATES, ""))
            cache_file = user_input.get(CONF_CACHE_FILE, DEFAULT_CACHE_FILE)
            if not str(cache_file).startswith("/"):
                cache_file = self.hass.config.path(str(cache_file))

            client = GuardSaaSClient(
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                cache_file=str(cache_file),
                mandatory_plates=mandatory_plates,
            )

            try:
                result = await self.hass.async_add_executor_job(client.update)
            except Exception:
                result = {"authenticated": False}

            if not result.get("authenticated"):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_MANDATORY_PLATES: mandatory_plates,
                        CONF_UPDATE_INTERVAL_HOURS: float(user_input[CONF_UPDATE_INTERVAL_HOURS]),
                        CONF_CACHE_FILE: user_input.get(CONF_CACHE_FILE, DEFAULT_CACHE_FILE),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(
                    CONF_MANDATORY_PLATES,
                    default=_plates_to_string(DEFAULT_MANDATORY_PLATES),
                ): str,
                vol.Optional(CONF_UPDATE_INTERVAL_HOURS, default=DEFAULT_UPDATE_INTERVAL_HOURS): vol.All(vol.Coerce(float), vol.Range(min=0.01)),
                vol.Optional(CONF_CACHE_FILE, default=DEFAULT_CACHE_FILE): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Create options flow."""
        return GuardSaaSPlatesOptionsFlow(config_entry)


class GuardSaaSPlatesOptionsFlow(config_entries.OptionsFlow):
    """Options flow for GuardSaaS Plates."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_MANDATORY_PLATES: _plates_from_string(user_input.get(CONF_MANDATORY_PLATES, "")),
                    CONF_UPDATE_INTERVAL_HOURS: float(user_input[CONF_UPDATE_INTERVAL_HOURS]),
                    CONF_CACHE_FILE: user_input.get(CONF_CACHE_FILE, DEFAULT_CACHE_FILE),
                },
            )

        mandatory = self._config_entry.options.get(
            CONF_MANDATORY_PLATES,
            self._config_entry.data.get(CONF_MANDATORY_PLATES, DEFAULT_MANDATORY_PLATES),
        )
        if CONF_UPDATE_INTERVAL_HOURS in self._config_entry.options:
            update_interval_hours = _hours_from_entry_value(self._config_entry.options[CONF_UPDATE_INTERVAL_HOURS])
        elif CONF_UPDATE_INTERVAL_HOURS in self._config_entry.data:
            update_interval_hours = _hours_from_entry_value(self._config_entry.data[CONF_UPDATE_INTERVAL_HOURS])
        else:
            legacy_seconds = self._config_entry.options.get(
                CONF_SCAN_INTERVAL,
                self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            )
            update_interval_hours = _legacy_seconds_to_hours(legacy_seconds)
        cache_file = self._config_entry.options.get(
            CONF_CACHE_FILE,
            self._config_entry.data.get(CONF_CACHE_FILE, DEFAULT_CACHE_FILE),
        )

        schema = vol.Schema(
            {
                vol.Optional(CONF_MANDATORY_PLATES, default=_plates_to_string(mandatory)): str,
                vol.Optional(CONF_UPDATE_INTERVAL_HOURS, default=update_interval_hours): vol.All(vol.Coerce(float), vol.Range(min=0.01)),
                vol.Optional(CONF_CACHE_FILE, default=cache_file): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
