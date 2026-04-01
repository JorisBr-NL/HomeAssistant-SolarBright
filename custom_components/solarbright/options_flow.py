import voluptuous as vol
from homeassistant import config_entries

DEFAULT_POLL_INTERVAL = 30
DEFAULT_SKIP_NIGHT = True


class SolarBrightOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle SolarBright options."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict | None = None
    ):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "poll_interval",
                    default=self.config_entry.options.get(
                        "poll_interval", DEFAULT_POLL_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
                vol.Optional(
                    "skip_night",
                    default=self.config_entry.options.get(
                        "skip_night", DEFAULT_SKIP_NIGHT
                    ),
                ): bool,
            }),
        )
