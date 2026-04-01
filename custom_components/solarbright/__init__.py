from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SolarBrightCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = SolarBrightCoordinator(hass, entry.data["host"])
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True
