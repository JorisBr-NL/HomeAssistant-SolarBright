"""Constants for the SolarBright integration."""

from homeassistant.const import Platform

DOMAIN = "solarbright"
PLATFORMS = [Platform.SENSOR]

# Config entry data (besides CONF_HOST)
CONF_SERIAL = "serial"
CONF_MODEL = "model"
CONF_RATED_POWER = "rated_power"

# Options
CONF_POLL_INTERVAL = "poll_interval"
CONF_SKIP_NIGHT = "skip_night"
DEFAULT_POLL_INTERVAL = 60  # seconds
MIN_POLL_INTERVAL = 5
MAX_POLL_INTERVAL = 3600
DEFAULT_SKIP_NIGHT = True

# After this many failed reads in a row the inverter counts as offline: power
# drops to 0 W. A single missed read (Wi-Fi hiccup) keeps the last values.
OFFLINE_AFTER_FAILURES = 3

# Values of the status sensor
STATUS_ONLINE = "online"
STATUS_OFFLINE = "offline"
STATUS_NIGHT = "night"
STATUSES = [STATUS_ONLINE, STATUS_OFFLINE, STATUS_NIGHT]
