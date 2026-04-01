import logging
import re
from datetime import timedelta

import aiohttp

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SolarInverterCoordinator(DataUpdateCoordinator):
    """Coordinator for SolarBright inverter."""

    def __init__(self, hass, entry):
        """Initialize coordinator."""
        self.hass = hass
        self.host = entry.data["host"]

        # Options (from options_flow)
        self.poll_interval = entry.options.get("poll_interval", DEFAULT_SCAN_INTERVAL)
        self.skip_night = entry.options.get("skip_night", True)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.host}",
            update_interval=timedelta(seconds=self.poll_interval),
        )

    async def _async_update_data(self):
        """Fetch data from inverter."""

        # 🌙 Skip polling at night if enabled
        if self.skip_night:
            sun = self.hass.states.get("sun.sun")
            if sun and sun.state == "below_horizon":
                _LOGGER.debug("SolarBright: Nighttime, skipping update")
                return self.data  # keep last known data

        url = f"http://{self.host}/js/status.js"
        session = async_get_clientsession(self.hass)

        try:
            _LOGGER.debug("Fetching inverter data from %s", url)

            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP error {resp.status}")

                text = await resp.text()

        except (aiohttp.ClientError, TimeoutError) as err:
            # ⚡ Do NOT spam errors at night or temporary outages
            _LOGGER.warning("SolarBright inverter unreachable: %s", err)
            return self.data  # keep previous data

        # Parse JS response
        match = re.search(r'webData="([^"]+)"', text)

        if not match:
            raise UpdateFailed("webData not found")

        data = match.group(1).split(",")

        try:
            parsed = {
                "serial": data[0],
                "model": data[3],
                "rated_power": int(data[4] or 0),
                "current_power": int(data[5] or 0),
                "daily_energy": int(data[6] or 0) / 100,
                "total_energy": int(data[7] or 0) / 10,
                "status": data[9] if len(data) > 9 else "unknown",
            }

            return parsed

        except Exception as err:
            raise UpdateFailed(f"Parsing error: {err}")
