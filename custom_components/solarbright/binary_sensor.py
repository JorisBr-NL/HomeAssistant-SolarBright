from homeassistant.components.binary_sensor import BinarySensorEntity
from .coordinator import GLOBAL_COORDINATORS

class SolarBrightOfflineSensor(BinarySensorEntity):
    def __init__(self):
        self._attr_name = "SolarBright Any Inverter Offline"
        self._attr_unique_id = "solarbright_any_offline"

    @property
    def is_on(self):
        return any(not c.last_update_success for c in GLOBAL_COORDINATORS)

class SolarBrightNoProductionSensor(BinarySensorEntity):
    def __init__(self):
        self._attr_name = "SolarBright No Production"
        self._attr_unique_id = "solarbright_no_production"

    @property
    def is_on(self):
        total = sum(c.data.get("power", 0) for c in GLOBAL_COORDINATORS if c.data)
        return total < 5
