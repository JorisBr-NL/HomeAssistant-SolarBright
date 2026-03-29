import aiohttp
import logging
import re
from datetime import timedelta, datetime
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.sun import get_astral_event_date

from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

SUN_MARGIN = timedelta(minutes=30)

async def fetch_data(session, ip):
    ip = ip.strip().replace("http://", "").replace("https://", "")
    url = f"http://{ip}/js/status.js"

    async with session.get(url, timeout=10) as resp:
        text = await resp.text()

    match = re.search(r'var webData="([^"]+)"', text)
    if not match:
        raise ValueError("webData not found")

    data = match.group(1).split(",")

    return {
        "current_power": int(data[5]),             # W
        "daily_energy": round(int(data[6]) / 100, 2),  # kWh
        "total_energy": round(int(data[7]) / 100, 2),  # kWh
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
        now = datetime.now(self.hass.config.time_zone)
        sunrise = get_astral_event_date(self.hass, "sunrise").astimezone()
        sunset = get_astral_event_date(self.hass, "sunset").astimezone()

        poll_start = sunrise - SUN_MARGIN
        poll_end = sunset + SUN_MARGIN

        if not (poll_start <= now <= poll_end):
            # Outside daylight hours → return 0 for power
            if hasattr(self, "data") and self.data:
                return {
                    "current_power": 0,
                    "daily_energy": self.data.get("daily_energy", 0),
                    "total_energy": self.data.get("total_energy", 0),
                }
            return {
                "current_power": 0,
                "daily_energy": 0,
                "total_energy": 0,
            }

        # Normal polling
        return await fetch_data(self.session, self.ip)
