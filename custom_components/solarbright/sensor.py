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
    coordinators = list(hass.data[DOMAIN].values())

    entities = []
    # Individual inverter sensors
    for coord in coordinators:
        for key, name, unit, device_class, state_class in SENSORS:
            entities.append(SolarBrightSensor(coord, key, name, unit, device_class, state_class))

    # Combined sensors
    entities.append(CombinedEnergySensor(hass, coordinators, "current_power", "Combined Power", "W", SensorDeviceClass.POWER, None))
    entities.append(CombinedEnergySensor(hass, coordinators, "daily_energy", "Combined Daily Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL))
    entities.append(CombinedEnergySensor(hass, coordinators, "total_energy", "Combined Total Energy", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING))

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


class CombinedEnergySensor(SensorEntity):
    """Virtual sensor to combine all inverters."""

    def __init__(self, hass, coordinators, key, name, unit, device_class, state_class):
        self.hass = hass
        self.coordinators = coordinators
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = f"combined_{key}"

    @property
    def native_value(self):
        total = 0
        for coord in self.coordinators:
            if coord.data and self._key in coord.data:
                total += coord.data[self._key]
        return round(total, 2)

    @property
    def device_info(self):
        return {
            "identifiers": {("solarbright_combined", "all")},
            "name": "Combined SolarBright Inverters",
            "manufacturer": "SolarBright",
        }

    async def async_update(self):
        for coord in self.coordinators:
            await coord.async_request_refresh()
