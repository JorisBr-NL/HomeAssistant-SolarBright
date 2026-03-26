import aiohttp
import async_timeout
import re
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DEFAULT_SCAN_INTERVAL

GLOBAL_COORDINATORS = []

class SolarBrightCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host, port):
        super().__init__(
            hass,
            logger=hass.logger,
            name=f"solarbright_{host}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.host = host
        self.port = port
        self.fail_count = 0
        GLOBAL_COORDINATORS.append(self)

    async def _async_update_data(self):
        url = f"http://{self.host}:{self.port}/js/status.js"
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    resp = await session.get(url)
                    if resp.status != 200:
                        raise Exception(f"HTTP {resp.status}")
                    text = await resp.text()

            var_map = self._parse_vars(text)
            fields = self._parse_csv(var_map.get("webData", ""))

            if len(fields) < 8:
                raise Exception("Invalid data")

            rated = float(fields[4])
            current = float(fields[5])

            self.fail_count = 0

            return {
                "power": current,
                "power_pct": round(current / rated * 100, 1),
                "daily": float(fields[6]) / 10,
                "total": float(fields[7]) / 100,
                "rated": rated,
                "model": fields[3],
                "firmware": f"{fields[1]}_{fields[2]} ({var_map.get('version')})",
                "fail_count": self.fail_count,
                "available": True,
            }

        except Exception as e:
            self.fail_count += 1
            if self.fail_count >= 10:
                raise UpdateFailed("Too many failures")
            raise UpdateFailed(f"Inverter error: {e}")

    def _parse_vars(self, text):
        return dict(re.findall(r'var\s+(\w+)\s*=\s*"([^"]*)";', text))

    def _parse_csv(self, csv):
        return [x.strip() for x in csv.split(",")]
