import aiohttp
import logging
import re
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

SUN_MARGIN = timedelta(minutes=30)

async def fetch_data(session, ip):
    """Fetch data from inverter API."""
    ip = ip.strip().replace("http://", "").replace("https://", "")
    url = f"http://{ip}/js/status.js"

    async with session.get(url, timeout=10) as resp:
        text = await resp.text()

    match = re.search(r'var webData="([^"]+)"', text)
    if not match:
        raise ValueError("webData not found")

    data = match.group(1).split(",")

    return {
        "current_power": int(data[5]),                # W
        "daily_energy": round(int(data[6]) / 100, 2), # kWh
        "total_energy": round(int(data[7]) / 100, 2), # kWh
    }


class SolarBrightCoordinator(DataUpdateCoordinator):
    """Coordinator for a single inverter."""

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
        """Poll inverter data respecting sunrise/sunset."""
        now = dt_util.now()  # tz-aware datetime

        sun = self.hass.states.get("sun.sun")
        if sun:
            sunrise = sun.attributes.get("next_rising")
            sunset = sun.attributes.get("next_setting")
        else:
            # fallback if sun entity missing: poll all day
            sunrise = now - timedelta(hours=1)
            sunset = now + timedelta(hours=1)

        poll_start = sunrise - SUN_MARGIN
        poll_end = sunset + SUN_MARGIN

        if not (poll_start <= now <= poll_end):
            # Nighttime: return 0 power but preserve energy values if available
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

        # Daytime: normal polling
        return await fetch_data(self.session, self.ip)
