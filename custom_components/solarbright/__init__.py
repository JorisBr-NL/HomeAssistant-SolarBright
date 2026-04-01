from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .coordinator import SolarInverterCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = SolarInverterCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True
