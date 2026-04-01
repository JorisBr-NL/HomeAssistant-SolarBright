# SolarBright Inverter (Home Assistant)

Custom integration for Hosala SolarBright inverters via local API.

## Author

This integration was written and maintained by **Joris Bakker**.

# Solar Inverter (JS API) - Home Assistant

Custom HACS integration for solar inverters exposing data via `/js/status.js`.

## Features

- Live power (W)
- Daily energy (kWh)
- Total energy (kWh)
- Energy Dashboard compatible

## Installation

### HACS
1. Add this repo as a custom repository
2. Install integration
3. Restart Home Assistant

### Manual
Copy `custom_components/solar_inverter` into your HA config folder.

## Configuration

Go to:
Settings → Devices & Services → Add Integration → "Solar Inverter"

Enter:
- Host (e.g. `192.168.2.2`)

## Notes
Tested with SolarBright 4.2kW & 3kW inverter.
