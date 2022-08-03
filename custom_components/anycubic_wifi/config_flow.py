"""Config flow for Anycubic 3D Printer."""
from __future__ import annotations

import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import dhcp
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_MODEL
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback
from uart_wifi.response import MonoXSysInfo
from uart_wifi.errors import ConnectionException
from .const import (
    API_FIRMWARE,
    API_MODEL,
    API_SERIAL,
    CONF_DHCP,
    OPT_HIDE_EXTRA_SENSORS,
    OPT_USE_PICTURE,
    SW_VERSION,
)
from .errors import AnycubicException
from .adapter_fascade import MonoXAPIAdapter
from .options import AnycubicOptionsFlowHandler
from .const import CONF_SERIAL, DOMAIN, OPT_HIDE_IP, OPT_NO_EXTRA_DATA

# Schema used for initalization of the config flow
DETECTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.1.254"): str,
    }
)

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class MyConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Anycubic config flow."""

    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow."""
        return AnycubicOptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        """Initialize the Anycubic MonoX config flow."""
        self.device_config = {}
        self.discovery_schema = {}
        self.import_schema = {}
        self.serial = None
        self.data: dict = {}

    async def async_step_dhcp(
        self, discovery_info: dhcp.DhcpServiceInfo
    ) -> FlowResult:
        """This is where the Home Assistant calls up this config flow with any
        discovered devices, matching the dhcp profile specified in the
        manifest.json. Here we create a dictionary and pass it on to the next
        steps in the config flow.  The overall flow from this point is
        dhcp->duplicate_detection->user confirmation."""
        if discovery_info.ip is not None:
            discovered_information = {
                CONF_HOST: str(discovery_info.ip),
                CONF_DHCP: True,
            }
            try:
                configured: bool = await self.async_step_duplicates(
                    discovered_information
                )
                # Before adding the device, we pass it into the user
                # confirmation step.
                if configured:
                    return await self.async_step_user()
                return False
            except ValueError:
                # Don't spam the logs because this device just came back online
                # and we already have a config entry for it.
                return False

    async def async_step_user(self, user_input=None) -> FlowResult:
        """This is where the user or DHCP will provide a host. From there we
        query the device to see if it is duplicated. When launched manually,
        no user input is present, so we show the form. If launched from DHCP,
        we show the user the device information and ask if it is correct."""
        if user_input is not None and not hasattr(user_input, CONF_DHCP):
            try:
                configured: bool = await self.async_step_duplicates(user_input)
                if not configured:
                    return self.async_abort(reason="duplicate_detection")
                return await self.async_step_finish(user_input)
            except ValueError:
                user_input["errors"] = ["connection_error"]
                return await self.async_step_user()
        return self.async_show_form(
            step_id="user",
            description_placeholders=user_input,
            data_schema=DETECTION_SCHEMA,
            errors=user_input["errors"]
            if hasattr(user_input, "errors")
            else None,
        )

    async def async_step_duplicates(self, device: dict) -> bool:
        """Prepare configuration for a discovered Anycubic device. Before continuing,
        we check if the serial number is already registered to a device.
        :param device: The device dictionary from the discovery event.
        :return: True if the device is configured, False if not."""
        # Abort if serial is configured
        self._add_device_info_to_device(device)
        if CONF_SERIAL not in device:
            self.async_abort(reason="not_enough_data")
        await self.async_set_unique_id(device[CONF_SERIAL])

        self._abort_if_unique_id_configured(
            updates={CONF_HOST: device[CONF_HOST]}
        )
        # Check entries to see if they have been discovered previously
        entries = self._async_current_entries()
        for entry in entries:
            if entry.data[CONF_SERIAL] == device[CONF_SERIAL]:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        **entry.data,
                        CONF_HOST: device[CONF_HOST],
                    },
                )
                self.async_abort(reason="already_configured")
                return False  # Already configured
        return True

    def _add_device_info_to_device(self, device):
        adapter = MonoXAPIAdapter(device[CONF_HOST])
        system_information: MonoXSysInfo() = adapter.sysinfo()
        device.update(self.map_sysinfo_to_data(system_information))

    async def async_step_finish(
        self, discovered_information: dict
    ) -> FlowResult:
        """Gather information from a discovered device.  This is the final step
        in the config flow. We perform final checks and then gather the system
        information and especially record the serial number as a device-unique
        identifier for the config entry. Information is updated and then pushed
        to Home Assistant as a config entry."""
        if discovered_information[CONF_HOST] is not None:
            try:
                self.data[CONF_HOST] = discovered_information[CONF_HOST]
                adapter = MonoXAPIAdapter(self.data[CONF_HOST])
                system_information = adapter.sysinfo()
                if system_information is None:
                    return

                self.data.update(self.map_sysinfo_to_data(system_information))

                await self.async_set_unique_id(self.data[CONF_SERIAL])

                self.context.update(
                    {
                        "title_placeholders": {
                            CONF_HOST: self.data[CONF_HOST],
                        }
                    }
                )

                return self.async_create_entry(
                    title=self.data[CONF_MODEL],
                    data=self.data,
                    options={
                        OPT_HIDE_IP: False,
                        OPT_NO_EXTRA_DATA: False,
                        OPT_HIDE_EXTRA_SENSORS: False,
                        OPT_USE_PICTURE: False,
                    },
                    description="Anycubic Uart Device",
                )

            except (AnycubicException, ConnectionException) as ex:
                _LOGGER.error("Exception while processing device data %s", ex)
                return await self.async_step_user()

    def map_sysinfo_to_data(self, sysinfo: MonoXSysInfo) -> dict:
        """Map the sysInfo result to a dictionary.  This is used to create the
        config entry."""
        data: dict = {}
        if hasattr(sysinfo, API_FIRMWARE):
            data[SW_VERSION] = sysinfo.firmware
        if hasattr(sysinfo, API_MODEL):
            data[CONF_MODEL] = sysinfo.model
        if hasattr(sysinfo, API_MODEL):
            data[CONF_NAME] = sysinfo.model
        if hasattr(sysinfo, API_SERIAL):
            data[CONF_SERIAL] = sysinfo.serial
        return data
