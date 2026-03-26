async def async_get_config_entry_diagnostics(hass, entry):
    return {
        "entry": entry.data,
        "state": "ok"
    }
