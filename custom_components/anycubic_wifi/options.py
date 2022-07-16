"""Options flow handler provides options to users."""

from typing import Any
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol
from .const import OPT_HIDE_IP, OPT_NO_EXTRA_DATA, OPT_HIDE_EXTRA_SENSORS, OPT_USE_PICTURE


class AnycubicOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options provided to the user."""

    def __init__(self, config_entry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self,
                              user_input: dict[str, Any] | None = None
                              ) -> FlowResult:
        """Manage the options. We display the options to the user from
        this location. The first pass through we will create a form to
        collect the options. The second pass will save them to the
        config_entry."""
        if user_input is not None:
            return self.async_create_entry(title="asdfasdf", data=user_input)

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
                    bool,
                    vol.Required(
                        OPT_USE_PICTURE,
                        default=self.config_entry.options.get(OPT_USE_PICTURE),
                    ):
                    bool
                }, ))
