DOMAIN = "solar_inverter"

CONF_HOST = "host"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_DAY_OFFSET = "day_offset"

DEFAULT_SCAN_INTERVAL = 120  # seconds
DEFAULT_DAY_OFFSET = 30      # minutes before/after sun
NIGHT_SCAN_INTERVAL = 1800    # 30 min fallback at night
