from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.const import UnitOfPower, UnitOfEnergy
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up SolarBright sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            SolarBrightPowerSensor(coordinator, entry),
            SolarBrightDailyEnergySensor(coordinator, entry),
            SolarBrightTotalEnergySensor(coordinator, entry),
        ]
    )


class SolarBrightBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for SolarBright sensors."""

    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator)
        self._entry = entry
        self._key = key

        self._attr_name = f"SolarBright {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    @property
    def device_info(self):
        """Return device info for grouping."""
        data = self.coordinator.data or {}

        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "SolarBright Inverter",
            "manufacturer": "SolarBright",
            "model": data.get("model", "Unknown"),
            "serial_number": data.get("serial"),
        }

    @property
    def available(self):
        """Entity availability."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self):
        """Return sensor value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._key)


# 🔋 Power Sensor
class SolarBrightPowerSensor(SolarBrightBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "current_power", "Power")

        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_state_class = SensorStateClass.MEASUREMENT


# 📅 Daily Energy Sensor (Energy Dashboard compatible)
class SolarBrightDailyEnergySensor(SolarBrightBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "daily_energy", "Daily Energy")

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING


# 📊 Total Energy Sensor
class SolarBrightTotalEnergySensor(SolarBrightBaseSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "total_energy", "Total Energy")

        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
