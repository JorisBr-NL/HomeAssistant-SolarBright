from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

import aiohttp

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
    }
)

async def validate_host(hass: HomeAssistant, host: str) -> bool:
    """Validate that we can reach the SolarBright inverter."""
    url = f"http://{host}/js/status.js"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                return response.status == 200
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return False

class SolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        errors = {}

        if user_input is not None:
            host = user_input["host"].strip()

            # Prevent duplicate entries
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            # Validate the inverter
            valid = await validate_host(self.hass, host)
            if not valid:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Inverter ({host})",
                    data={"host": host},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
