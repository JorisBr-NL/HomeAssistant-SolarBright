"""Setup, sensors and offline behaviour."""

import aiohttp
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.solarbright.const import CONF_SERIAL, DOMAIN

from .conftest import HOST, SERIAL, URL, status_js

POWER = "sensor.solarbright_h0000test01_power"
DAILY = "sensor.solarbright_h0000test01_daily_energy"
TOTAL = "sensor.solarbright_h0000test01_total_energy"
STATUS = "sensor.solarbright_h0000test01_status"


def _entry(**data) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=data.get(CONF_SERIAL, HOST),
        data={CONF_HOST: HOST, **data},
        title="SolarBright",
    )


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _refresh(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


def _state(hass: HomeAssistant, entity_id: str) -> str:
    return hass.states.get(entity_id).state


async def test_sensors(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, text=status_js())
    entry = _entry(serial=SERIAL)
    await _setup(hass, entry)

    assert entry.state is ConfigEntryState.LOADED
    assert _state(hass, POWER) == "1234"
    assert float(_state(hass, DAILY)) == pytest.approx(15.67)
    assert float(_state(hass, TOTAL)) == pytest.approx(9876.5)
    assert _state(hass, STATUS) == "online"
    assert _state(hass, "sensor.solarbright_h0000test01_rated_power") == "4200"
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    assert device.serial_number == SERIAL
    assert device.model == "SB-TEST"


async def test_offline_after_three_failed_reads(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, text=status_js())
    entry = _entry(serial=SERIAL)
    await _setup(hass, entry)

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, exc=aiohttp.ClientError())
    await _refresh(hass, entry)
    await _refresh(hass, entry)
    assert _state(hass, POWER) == "1234"  # a hiccup keeps the last value
    assert _state(hass, STATUS) == "online"

    await _refresh(hass, entry)
    assert _state(hass, POWER) == "0"
    assert _state(hass, STATUS) == "offline"
    assert float(_state(hass, TOTAL)) == pytest.approx(9876.5)  # counters keep their value

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, text=status_js(power="800"))
    await _refresh(hass, entry)
    assert _state(hass, POWER) == "800"
    assert _state(hass, STATUS) == "online"


async def test_zero_total_glitch_is_ignored(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, text=status_js())
    entry = _entry(serial=SERIAL)
    await _setup(hass, entry)

    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, text=status_js(total="0", daily=""))
    await _refresh(hass, entry)
    assert float(_state(hass, TOTAL)) == pytest.approx(9876.5)
    assert float(_state(hass, DAILY)) == pytest.approx(15.67)


async def test_start_while_inverter_sleeps(hass: HomeAssistant, aioclient_mock) -> None:
    """With a known serial the integration starts without the inverter."""
    aioclient_mock.get(URL, exc=aiohttp.ClientError())
    entry = _entry(serial=SERIAL)
    await _setup(hass, entry)

    assert entry.state is ConfigEntryState.LOADED
    assert _state(hass, POWER) == "0"
    assert _state(hass, STATUS) == "offline"


async def test_start_without_serial_and_inverter_offline_retries(
    hass: HomeAssistant, aioclient_mock
) -> None:
    aioclient_mock.get(URL, exc=aiohttp.ClientError())
    entry = _entry()
    await _setup(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_night_skips_polling(hass: HomeAssistant, aioclient_mock) -> None:
    hass.states.async_set("sun.sun", "below_horizon")
    aioclient_mock.get(URL, text=status_js())
    entry = _entry(serial=SERIAL)
    await _setup(hass, entry)

    assert aioclient_mock.call_count == 0
    assert _state(hass, POWER) == "0"
    assert _state(hass, STATUS) == "night"


async def test_upgrade_from_1_0_keeps_entity_ids(hass: HomeAssistant, aioclient_mock) -> None:
    """1.0 entries: unique ID was the host, no serial stored, old-style entity IDs."""
    aioclient_mock.get(URL, text=status_js())
    entry = _entry()
    entry.add_to_hass(hass)
    old_power = "sensor.solarbright_inverter_old_solarbright_power"
    er.async_get(hass).async_get_or_create(
        "sensor",
        DOMAIN,
        f"{entry.entry_id}_current_power",
        config_entry=entry,
        suggested_object_id="solarbright_inverter_old_solarbright_power",
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.unique_id == SERIAL
    assert entry.data[CONF_SERIAL] == SERIAL
    assert _state(hass, old_power) == "1234"


async def test_upgrade_takes_serial_from_device_registry(
    hass: HomeAssistant, aioclient_mock
) -> None:
    """A 1.0 entry starting at night can still load: the device registry knows the serial."""
    aioclient_mock.get(URL, exc=aiohttp.ClientError())
    entry = _entry()
    entry.add_to_hass(hass)
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        serial_number=SERIAL,
        model="Unknown",
    )
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.data[CONF_SERIAL] == SERIAL
    assert "model" not in entry.data


async def test_unload(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, text=status_js())
    entry = _entry(serial=SERIAL)
    await _setup(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED
