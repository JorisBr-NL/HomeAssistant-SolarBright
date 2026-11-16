"""Config, reconfigure and options flow."""

import aiohttp
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.solarbright.const import (
    CONF_POLL_INTERVAL,
    CONF_SERIAL,
    CONF_SKIP_NIGHT,
    DOMAIN,
)

from .conftest import HOST, SERIAL, URL, status_js

NEW_HOST = "192.0.2.20"
NEW_URL = f"http://{NEW_HOST}/js/status.js"


def _entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN, unique_id=SERIAL, data={CONF_HOST: HOST, CONF_SERIAL: SERIAL}
    )


async def test_user_flow(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, text=status_js())
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: f" http://{HOST}/ "}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"SolarBright {SERIAL}"
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_SERIAL] == SERIAL
    assert result["result"].unique_id == SERIAL


async def test_user_flow_cannot_connect(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, exc=aiohttp.ClientError())
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data={CONF_HOST: HOST}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_not_an_inverter(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, text="<html>router</html>")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data={CONF_HOST: HOST}
    )
    assert result["errors"] == {"base": "invalid_response"}


async def test_same_inverter_new_address_updates_entry(
    hass: HomeAssistant, aioclient_mock
) -> None:
    entry = _entry()
    entry.add_to_hass(hass)
    aioclient_mock.get(NEW_URL, text=status_js())
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data={CONF_HOST: NEW_HOST}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == NEW_HOST


async def test_reconfigure(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, text=status_js())
    aioclient_mock.get(NEW_URL, text=status_js())
    entry = _entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: NEW_HOST}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == NEW_HOST


async def test_reconfigure_other_inverter(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(NEW_URL, text=status_js(serial="H0000TEST02"))
    entry = _entry()
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: NEW_HOST}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"
    assert entry.data[CONF_HOST] == HOST


async def test_options_flow_changes_interval(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, text=status_js())
    entry = _entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_POLL_INTERVAL: 30.0, CONF_SKIP_NIGHT: False}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_POLL_INTERVAL: 30, CONF_SKIP_NIGHT: False}
    # The entry was reloaded with the new interval.
    assert entry.runtime_data.update_interval.total_seconds() == 30
    assert entry.runtime_data.skip_night is False
