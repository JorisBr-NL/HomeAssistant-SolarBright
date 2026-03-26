from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, DATA_COORDINATORS
from .forecast_coordinator import SolarForecastCoordinator

PLATFORMS = ["sensor", "binary_sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_COORDINATORS, {})

    # Setup forecast coordinator (shared)
    if "forecast" not in hass.data[DOMAIN]:
        forecast_coordinator = SolarForecastCoordinator(hass)
        await forecast_coordinator.async_config_entry_first_refresh()
        hass.data[DOMAIN]["forecast"] = forecast_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
