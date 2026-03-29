from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfPower, UnitOfEnergy
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from .const import DOMAIN


SENSORS = [
    ("current_power", "Current Power", UnitOfPower.WATT, SensorDeviceClass.POWER, None),
    ("daily_energy", "Daily Energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL),
    ("total_energy", "Total Energy", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SolarBrightSensor(coordinator, key, name, unit, device_class, state_class)
        for key, name, unit, device_class, state_class in SENSORS
    ]

    async_add_entities(entities)


class SolarBrightSensor(SensorEntity):
    def __init__(self, coordinator, key, name, unit, device_class, state_class):
        self.coordinator = coordinator
        self._key = key

        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = f"{coordinator.ip}_{key}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    @property
    def device_info(self):
        return {
            "identifiers": {("solarbright", self.coordinator.ip)},
            "name": f"SolarBright {self.coordinator.ip}",
            "manufacturer": "SolarBright",
        }

    async def async_update(self):
        await self.coordinator.async_request_refresh()
