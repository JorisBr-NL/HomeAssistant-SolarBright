"""The SolarBright inverter integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_MODEL, CONF_SERIAL, DOMAIN, PLATFORMS
from .coordinator import SolarBrightCoordinator

_LOGGER = logging.getLogger(__name__)

type SolarBrightConfigEntry = ConfigEntry[SolarBrightCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SolarBrightConfigEntry) -> bool:
    """Set up SolarBright from a config entry."""
    _adopt_serial_from_device_registry(hass, entry)

    coordinator = SolarBrightCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    _store_device_details(hass, entry, coordinator)

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SolarBrightConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass: HomeAssistant, entry: SolarBrightConfigEntry) -> None:
    """Apply new options (poll interval, night skip) by reloading."""
    await hass.config_entries.async_reload(entry.entry_id)


def _adopt_serial_from_device_registry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Entries made by version 1.0 only stored the host.

    The device registry still knows the serial and model from earlier runs; copy them
    into the entry so the integration can start while the inverter sleeps.
    """
    if entry.data.get(CONF_SERIAL):
        return
    device = _device_of_entry(hass, entry)
    if device is None or not device.serial_number or device.serial_number == "unknown":
        return
    data = {**entry.data, CONF_SERIAL: device.serial_number}
    if device.model and device.model != "Unknown":  # 1.0 used "Unknown" as placeholder
        data[CONF_MODEL] = device.model
    hass.config_entries.async_update_entry(entry, data=data)


def _device_of_entry(hass: HomeAssistant, entry: ConfigEntry) -> dr.DeviceEntry | None:
    """The inverter device of this entry (one device per entry)."""
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    return next((d for d in devices if (DOMAIN, entry.entry_id) in d.identifiers), None)


def _store_device_details(
    hass: HomeAssistant, entry: ConfigEntry, coordinator: SolarBrightCoordinator
) -> None:
    """Keep serial, model and rated power in the entry and use the serial as unique ID.

    Version 1.0 used the host as unique ID, so a new IP address gave a duplicate entry.
    """
    details = {k: v for k, v in coordinator.device_details().items() if v is not None}
    serial = details.get(CONF_SERIAL)
    new_data = {**entry.data, **details}
    unique_id = entry.unique_id
    if serial and unique_id != serial:
        taken = hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, serial)
        if taken is None:
            unique_id = serial
        else:
            _LOGGER.warning(
                "Inverter %s is configured twice; remove one of the SolarBright entries", serial
            )
    if new_data != dict(entry.data) or unique_id != entry.unique_id:
        hass.config_entries.async_update_entry(entry, data=new_data, unique_id=unique_id)
