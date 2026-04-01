from __future__ import annotations

import asyncio
import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
    }
)


async def validate_host(hass: HomeAssistant, host: str) -> bool:
    """Validate inverter connectivity."""
    url = f"http://{host}/js/status.js"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                return resp.status == 200
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return False


class SolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle SolarBright config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors = {}

        if user_input is not None:
            host = user_input["host"].strip()

            # Prevent duplicates
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            # Validate connection
            if not await validate_host(self.hass, host):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"SolarBright ({host})",
                    data={"host": host},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
