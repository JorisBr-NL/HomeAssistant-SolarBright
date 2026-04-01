import re
import aiohttp
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


class SolarInverterCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.host = host

    async def _async_update_data(self):
        url = f"http://{self.host}/js/status.js"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    text = await resp.text()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")

        # Extract webData
        match = re.search(r'webData="([^"]+)"', text)
        if not match:
            raise UpdateFailed("webData not found")

        data = match.group(1).split(",")

        return {
            "serial": data[0],
            "model": data[3],
            "rated_power": int(data[4] or 0),
            "current_power": int(data[5] or 0),
            "daily_energy": int(data[6] or 0) / 100,
            "total_energy": int(data[7] or 0) / 10,
            "status": data[9] if len(data) > 9 else "unknown",
        }
