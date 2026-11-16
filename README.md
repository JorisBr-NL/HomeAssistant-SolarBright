# SolarBright Inverter (Home Assistant)

Custom integration for SolarBright (Hosola) solar inverters. It reads the inverter's
local web page `/js/status.js` over your own network; no cloud account is needed.

## Author

This integration was written and maintained by **Joris Bakker**.

## Sensors

| Sensor | Unit | Notes |
|---|---|---|
| Power | W | Live AC power. **0 W** when the inverter is offline or it is night. |
| Daily energy | kWh | Production today. The inverter resets it each morning. |
| Total energy | kWh | Lifetime production. Use this one in the Energy dashboard. |
| Status | – | `online`, `offline` or `night`. Attributes: the raw inverter status code and when it was last seen. |
| Rated power | W | Diagnostic: the nominal power of the inverter. |

The device in Home Assistant shows the serial number and model of the inverter.

## How it behaves when the inverter is off

SolarBright inverters switch off (including Wi-Fi) when there is no sun, and they are
also off when their breaker is switched off. The integration handles that like this:

- **One missed read** (a Wi-Fi hiccup): the last values stay.
- **Three missed reads in a row**: the status becomes `offline` and power becomes **0 W**.
  The energy sensors keep their last value, so the Energy dashboard does not see a gap.
- **At night** (optional, on by default): the inverter is not polled while `sun.sun` is
  below the horizon; status is `night` and power 0 W.
- **Glitches**: an empty or zero total from a starting inverter is ignored, and a sudden
  drop of a counter is only accepted when it is a normal daily reset or repeats for three
  reads. This prevents huge false spikes in the Energy dashboard.
- **Home Assistant restart at night**: the integration starts with the last known values;
  it does not wait for the inverter.

## Installation

### HACS
1. In HACS, add `https://github.com/JorisBr-NL/HomeAssistant-SolarBright` as a custom
   repository of type *Integration*.
2. Install **SolarBright Inverter**.
3. Restart Home Assistant.

### Manual
Copy `custom_components/solarbright` into the `custom_components` folder of your Home
Assistant configuration and restart Home Assistant.

## Configuration

Settings → Devices & services → Add integration → **SolarBright Inverter**.

Enter the IP address or host name of the inverter (for example `192.168.1.50`). The
inverter must be on (daylight) when you add it. Give the inverter a fixed IP address in
your router.

- **Change the address later:** open the integration, choose ⋮ → *Reconfigure*.
- **Options** (⚙ *Configure*): polling interval (default 60 s, 5–3600 s) and whether to
  skip polling at night.

## Upgrading from 1.0

Existing entities keep their entity IDs. On the first start the integration stores the
serial number of the inverter and uses it as the unique ID instead of the IP address.
The device is renamed to `SolarBright <serial>`; you can rename it again if you like.

## Compatibility

Tested with SolarBright 3 kW and 4.2 kW inverters. Requires Home Assistant 2025.1 or
newer; the logo in the integration list needs 2026.3 or newer.

## License

[MIT](LICENSE)
