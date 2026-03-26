import aiohttp
import async_timeout
from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pvlib import location, irradiance
from .const import DEFAULT_SCAN_INTERVAL, PANEL_AREA, PANEL_EFFICIENCY, PANEL_TILT, PANEL_AZIMUTH

LAT = 52.1
LON = 5.2
API_KEY = "YOUR_OPENWEATHERMAP_KEY"

class SolarForecastCoordinator(DataUpdateCoordinator):
    def __init__(self, hass):
        super().__init__(
            hass,
            logger=hass.logger,
            name="solarforecast",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.hourly_forecast = []
        self.daily_forecast = []

    async def _async_update_data(self):
        url = f"https://api.openweathermap.org/data/2.5/onecall?lat={LAT}&lon={LON}&exclude=minutely,current,alerts&appid={API_KEY}&units=metric"
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    resp = await session.get(url)
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status}")
                    data = await resp.json()

            loc = location.Location(LAT, LON)
            self.hourly_forecast = []
            for h in data["hourly"][:24]:
                ghi = h.get("uvi", 0) * 100  # rough approximation W/m²
                poa = irradiance.get_total_irradiance(
                    surface_tilt=PANEL_TILT,
                    surface_azimuth=PANEL_AZIMUTH,
                    dni=ghi,
                    ghi=ghi,
                    dhi=ghi
                )["poa_global"]
                kwh = PANEL_AREA * PANEL_EFFICIENCY * poa / 1000
                self.hourly_forecast.append(round(kwh, 2))

            self.daily_forecast = []
            for d in data["daily"][:3]:
                day_kwh = 0
                for h in range(24):
                    ghi = d.get("uvi", 0) * 100
                    poa = irradiance.get_total_irradiance(
                        surface_tilt=PANEL_TILT,
                        surface_azimuth=PANEL_AZIMUTH,
                        dni=ghi,
                        ghi=ghi,
                        dhi=ghi
                    )["poa_global"]
                    day_kwh += PANEL_AREA * PANEL_EFFICIENCY * poa / 1000
                self.daily_forecast.append(round(day_kwh, 2))

            return {
                "hourly": self.hourly_forecast,
                "daily": self.daily_forecast
            }

        except Exception as e:
            raise UpdateFailed(f"Forecast error: {e}")
