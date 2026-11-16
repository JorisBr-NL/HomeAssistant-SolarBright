"""Config, reconfigure and options flow for SolarBright."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, InvalidResponse, InverterReading, async_read_inverter, normalize_host
from .const import (
    CONF_MODEL,
    CONF_POLL_INTERVAL,
    CONF_RATED_POWER,
    CONF_SERIAL,
    CONF_SKIP_NIGHT,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_SKIP_NIGHT,
    DOMAIN,
    MAX_POLL_INTERVAL,
    MIN_POLL_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

HOST_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_POLL_INTERVAL): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=MIN_POLL_INTERVAL,
                max=MAX_POLL_INTERVAL,
                step=1,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement="s",
            )
        ),
        vol.Required(CONF_SKIP_NIGHT): selector.BooleanSelector(),
    }
)


def _entry_data(host: str, reading: InverterReading) -> dict[str, Any]:
    data: dict[str, Any] = {CONF_HOST: host, CONF_SERIAL: reading.serial}
    if reading.model:
        data[CONF_MODEL] = reading.model
    if reading.rated_power:
        data[CONF_RATED_POWER] = reading.rated_power
    return data


class SolarBrightConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a SolarBright inverter by its IP address or host name."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SolarBrightOptionsFlow:
        return SolarBrightOptionsFlow()

    async def _async_try_read(
        self, user_input: dict[str, Any], errors: dict[str, str]
    ) -> tuple[str, InverterReading | None]:
        host = normalize_host(user_input[CONF_HOST])
        try:
            reading = await async_read_inverter(async_get_clientsession(self.hass), host)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidResponse as err:
            _LOGGER.debug("Unexpected answer from %s: %s", host, err)
            errors["base"] = "invalid_response"
        else:
            return host, reading
        return host, None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host, reading = await self._async_try_read(user_input, errors)
            if reading is not None:
                await self.async_set_unique_id(reading.serial)
                # Same inverter on a new address: update the existing entry instead.
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(
                    title=f"SolarBright {reading.serial}", data=_entry_data(host, reading)
                )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(HOST_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the address of an inverter that is already set up."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            host, reading = await self._async_try_read(user_input, errors)
            if reading is not None:
                await self.async_set_unique_id(reading.serial)
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    entry, data_updates=_entry_data(host, reading)
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                HOST_SCHEMA, user_input or {CONF_HOST: entry.data[CONF_HOST]}
            ),
            errors=errors,
        )


class SolarBrightOptionsFlow(OptionsFlow):
    """Poll interval and night skip."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_POLL_INTERVAL: int(user_input[CONF_POLL_INTERVAL]),
                    CONF_SKIP_NIGHT: user_input[CONF_SKIP_NIGHT],
                }
            )
        current = {
            CONF_POLL_INTERVAL: DEFAULT_POLL_INTERVAL,
            CONF_SKIP_NIGHT: DEFAULT_SKIP_NIGHT,
            **self.config_entry.options,
        }
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(OPTIONS_SCHEMA, current),
        )
