from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import DeviceInfo
from .coordinator import GLOBAL_COORDINATORS
from .forecast_coordinator import SolarForecastCoordinator
from .const import DOMAIN

SENSORS = [
    ("power", "Power", "W", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    ("power_pct", "Power %", "%", None, SensorStateClass.MEASUREMENT),
    ("daily", "Daily Yield", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    ("total", "Total Yield", "kWh", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
    ("fail_count", "Fail Count", None, None, None),
]

FORECAST_SENSORS = [
    ("hourly", "Solar Forecast Next 24h", "kWh", None, None),
    ("daily", "Solar Forecast Next 3 Days", "kWh", None, None),
]

async def async_setup_entry(hass, entry, async_add_entities):
    entities = []

    coordinator = GLOBAL_COORDINATORS[0] if GLOBAL_COORDINATORS else None

    for key, name, unit, dev_class, state_class in SENSORS:
        entities.append(SolarBrightSensor(coordinator, entry, key, name, unit, dev_class, state_class))

    # Combined sensors
    entities.append(SolarBrightCombinedSensor("power", "Power", "W"))
    entities.append(SolarBrightCombinedSensor("daily", "Daily Yield", "kWh"))
    entities.append(SolarBrightCombinedSensor("total", "Total Yield", "kWh"))

    # Forecast sensors
    forecast = hass.data[DOMAIN]["forecast"]
    for key, name, unit, dev_class, state_class in FORECAST_SENSORS:
        entities.append(SolarForecastSensor(forecast, key, name, unit))

    async_add_entities(entities)

# … include previous SolarBrightSensor, SolarBrightCombinedSensor, SolarForecastSensor classes …
