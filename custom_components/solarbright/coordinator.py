import aiohttp
import logging
import re

from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def fetch_data(session, ip):
    url = f"http://{ip}/js/status.js"

    async with session.get(url, timeout=10) as resp:
        text = await resp.text()

    match = re.search(r'var webData="([^"]+)"', text)
    if not match:
        raise ValueError("webData not found")

    data = match.group(1).split(",")

    return {
        "current_power": int(data[5]),
        "daily_energy": int(data[6]) / 1000,
        "total_energy": int(data[7]) / 1000,
    }


class SolarBrightCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, session, ip):
        super().__init__(
            hass,
            _LOGGER,
            name=f"SolarBright {ip}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.session = session
        self.ip = ip

    async def _async_update_data(self):
        return await fetch_data(self.session, self.ip)
