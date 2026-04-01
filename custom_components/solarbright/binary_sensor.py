from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([InverterFaultSensor(coordinator)])

class InverterFaultSensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Inverter Fault"
        self._attr_unique_id = f"{coordinator.host}_fault"

    @property
    def is_on(self):
        return self.coordinator.data.get("status_code") == "4"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.host)}
        }
