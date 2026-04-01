from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfPower, UnitOfEnergy, PERCENTAGE
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data

    sensors = [
        SolarSensor(coordinator, "current_power", "Power", UnitOfPower.WATT),
        SolarSensor(coordinator, "daily_energy", "Daily Energy", UnitOfEnergy.KILO_WATT_HOUR, "energy", "total_increasing"),
        SolarSensor(coordinator, "total_energy", "Total Energy", UnitOfEnergy.KILO_WATT_HOUR, "energy", "total_increasing"),
        SolarSensor(coordinator, "rssi", "WiFi Signal", PERCENTAGE),
        SolarSensor(coordinator, "status_text", "Status"),
    ]

    async_add_entities(sensors)

class SolarSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, name, unit, device_class=None, state_class=None):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Inverter {name}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = f"{coordinator.host}_{key}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.host)},
            name=f"Solar Inverter ({self.coordinator.host})",
            manufacturer="Generic",
            model=self.coordinator.data.get("model"),
        )
