# SolarBright Inverter (Home Assistant)

Custom integration for SolarBright inverters via local API.

## Features
- Local polling (no cloud)
- Multiple inverter support
- Energy Dashboard compatible
- Automatic device grouping

## Installation (HACS)

1. Add this repo as a custom repository in HACS
2. Install "SolarBright Inverter"
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration
5. Enter your inverter IP

## Sensors

- Current Power (W)
- Daily Energy (kWh)
- Total Energy (kWh)

## Notes
Tested with SolarBright 4.2KW inverter.
