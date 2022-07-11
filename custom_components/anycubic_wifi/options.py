"""Options flow handler provides options to users."""

from typing import Any
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol
from .const import OPT_HIDE_IP, OPT_NO_EXTRA_DATA, OPT_HIDE_EXTRA_SENSORS


class AnycubicOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self,
                              user_input: dict[str, Any] | None = None
                              ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        OPT_HIDE_EXTRA_SENSORS,
                        default=self.config_entry.options.get(OPT_HIDE_EXTRA_SENSORS),
                    ):
                    bool,
                    vol.Required(
                        OPT_NO_EXTRA_DATA,
                        default=self.config_entry.options.get(OPT_NO_EXTRA_DATA),
                    ):
                    bool,
                    vol.Required(
                        OPT_HIDE_IP,
                        default=self.config_entry.options.get(OPT_HIDE_IP),
                    ):
                    bool
                    # ,
                    # vol.Required(
                    #     "extra_sensors",
                    #     default=self.config_entry.options.get("extra_sensors"),
                    # ):
                    # bool
                }, ),
        )
