"""Config flow for Anycubic 3D Printer."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import dhcp
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_MODEL
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback
from uart_wifi.response import MonoXSysInfo
from uart_wifi.errors import ConnectionException
from .const import OPT_HIDE_EXTRA_SENSORS, OPT_USE_PICTURE, SW_VERSION
from .errors import AnycubicException
from .adapter_fascade import MonoXAPIAdapter
from .options import AnycubicOptionsFlowHandler
from .const import (CONF_SERIAL, DOMAIN, OPT_HIDE_IP, OPT_NO_EXTRA_DATA)

LOGGER = logging.getLogger(__name__)

user_data_schema = vol.Schema({
    vol.Required(CONF_HOST, default="192.168.1.254"):
    str,
})

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
            self, discovery_info: dhcp.DhcpServiceInfo) -> FlowResult:
        """Prepare configuration for a DHCP discovered Anycubic uart-wifi device."""
        if discovery_info.ip is not None:
            discovered_information = {}
            discovered_information[CONF_HOST] = str(discovery_info.ip)
            self.data = {}
            self.async_step_duplicates(discovered_information)
            return await self.async_step_user()

    async def async_step_duplicates(self, device: dict) -> None:
        """Prepare configuration for a discovered Anycubic device."""
        #Abort if serial is configured
        self._add_device_info_to_device(device)
        await self.async_set_unique_id(device[CONF_SERIAL])
        self._abort_if_unique_id_configured(updates={
            CONF_HOST: device[CONF_HOST]
        })
        #Check entries to see if they have been discovered previously
        entries = self._async_current_entries()
        for entry in entries:
            if entry.data[CONF_SERIAL] == device[CONF_SERIAL]:
                self.hass.config_entries.async_update_entry(
                    entry, data={
                        **entry.data,
                        CONF_HOST: device[CONF_HOST],
                    })
            self.async_abort(reason="already_configured")

    async def async_step_import(self, user_input=None):
        """Occurs when a previously entry setup fails and is re-initiated."""
        return await self.async_step_user(user_input)
        #all checks passed, lets create the entry

    def _add_device_info_to_device(self, device):
        adapter = MonoXAPIAdapter(device[CONF_HOST])
        system_information: MonoXSysInfo() = adapter.sysinfo()
        device.update(self.map_sysinfo_to_data(system_information))

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle a Anycubic MonoX config flow start.

        Manage device specific parameters.
        """
        if user_input is not None:
            await self.async_step_duplicates(user_input)
            return await self.async_step_finish(user_input)
        return self.async_show_form(
            step_id="user",
            description_placeholders=user_input,
            data_schema=user_data_schema,
            errors={"0": "invalid_ip"},
        )

    async def async_step_finish(self,
                                discovered_information: dict) -> FlowResult:
        """Gather information from a discovered device"""
        if discovered_information[CONF_HOST] is not None:
            try:
                self.data[CONF_HOST] = discovered_information[CONF_HOST]
                adapter = MonoXAPIAdapter(self.data[CONF_HOST])
                system_information = adapter.sysinfo()
                if system_information is None:
                    return

                self.data.update(self.map_sysinfo_to_data(system_information))

                await self.async_set_unique_id(self.data[CONF_SERIAL])

                self.context.update({
                    "title_placeholders": {
                        CONF_HOST: self.data[CONF_HOST],
                    }
                })

                return self.async_create_entry(
                    title=self.data[CONF_MODEL],
                    data=self.data,
                    options={
                        OPT_HIDE_IP: False,
                        OPT_NO_EXTRA_DATA: False,
                        OPT_HIDE_EXTRA_SENSORS: False,
                        OPT_USE_PICTURE: False
                    },
                    description="Anycubic Uart Device",
                )

            except (AnycubicException, ConnectionException) as ex:
                _LOGGER.error("Exception while processing device data %s", ex)
                return await self.async_step_user()

    def map_sysinfo_to_data(self, sysinfo: MonoXSysInfo) -> dict:
        """map the sysInfo result to a dictionary"""
        data: dict = {}
        if hasattr(sysinfo, "firmware"):
            data[SW_VERSION] = sysinfo.firmware
        if hasattr(sysinfo, "model"):
            data[CONF_MODEL] = sysinfo.model
        if hasattr(sysinfo, "model"):
            data[CONF_NAME] = sysinfo.model
        if hasattr(sysinfo, "serial"):
            data[CONF_SERIAL] = sysinfo.serial
        return data
