import logging
import re
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, NIGHT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

# Status decoding
STATUS_MAP = {
    "0": "Offline",
    "1": "Standby",
    "2": "Starting",
    "3": "Running",
    "4": "Fault",
    "5": "Running",
}

class SolarInverterCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        self.hass = hass
        self.host = entry.data["host"]
        self.scan_interval = entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)
        self._is_daytime = True

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.host}",
            update_interval=timedelta(seconds=self.scan_interval),
        )

    async def _async_update_data(self):
        url = f"http://{self.host}/js/status.js"
        session = async_get_clientsession(self.hass)

        try:
            async with session.get(url, timeout=10) as resp:
                text = await resp.text()
        except Exception as err:
            raise UpdateFailed(f"Connection error: {err}")

        # Extract webData
        match = re.search(r'webData="([^"]+)"', text)
        if not match:
            raise UpdateFailed("webData not found")
        data = match.group(1).split(",")

        # RSSI
        rssi_match = re.search(r'm2mRssi="([^"]+)"', text)
        rssi = int(rssi_match.group(1).replace("%", "")) if rssi_match else None

        # Status code
        status_code = data[9] if len(data) > 9 else "unknown"

        return {
            "serial": data[0],
            "model": data[3],
            "rated_power": int(data[4] or 0),
            "current_power": int(data[5] or 0),
            "daily_energy": int(data[6] or 0) / 100,
            "total_energy": int(data[7] or 0) / 10,
            "status_code": status_code,
            "status_text": STATUS_MAP.get(status_code, "Unknown"),
            "rssi": rssi,
        }
