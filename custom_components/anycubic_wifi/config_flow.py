"""Config flow for Anycubic 3D Printer."""
from __future__ import annotations
import asyncio

import logging
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import dhcp
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from uart_wifi.response import MonoXSysInfo
from uart_wifi.errors import ConnectionException
from .const import SW_VERSION
from .errors import AnycubicException
from .mono_x_api_adapter_fascade import MonoXAPIAdapter

from .const import (
    CONF_MODEL,
    CONF_SERIAL,
    DOMAIN,
)

LOGGER = logging.getLogger(__name__)

user_data_schema = vol.Schema({
    vol.Required(CONF_HOST, default="192.168.1.254"):
    str,
})

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class MyConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Anycubic config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the Anycubic MonoX config flow."""
        self.device_config = {}
        self.discovery_schema = {}
        self.import_schema = {}
        self.serial = None
        self.data: dict = {}

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle a Anycubic MonoX config flow start.

        Manage device specific parameters.
        """
        errors = {}
        if user_input is not None:
            if user_input[CONF_HOST] is not None:
                return await self.process_discovered_device(user_input)
            errors = {"0": "invalid_ip"}
        else:

            return self.async_show_form(
                step_id="user",
                description_placeholders=user_input,
                data_schema=user_data_schema,
                errors=errors,
            )

    async def async_step_dhcp(
            self, discovery_info: dhcp.DhcpServiceInfo) -> FlowResult:
        """Prepare configuration for a DHCP discovered Anycubic uart-wifi device."""
        if discovery_info.ip is not None:
            discovered_information = {}
            discovered_information[CONF_HOST] = str(discovery_info.ip)
            self.data = {}
            return await self._process_discovered_device(discovered_information
                                                         )

    async def process_discovered_device(
            self, discovered_information: dict) -> FlowResult:
        """Gather information from a discovered device"""
        if discovered_information[CONF_HOST] is not None:
            try:
                adapter = MonoXAPIAdapter(discovered_information[CONF_HOST])
                system_information = await asyncio.wait_for(
                    adapter.sysinfo(), 5)
                self.data[CONF_HOST] = discovered_information[CONF_HOST]

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

    #https://github.com/home-assistant/core/blob/dev/homeassistant/components/axis/config_flow.py#L194
    async def _process_discovered_device(self, device: dict) -> Any:
        """Prepare configuration for a discovered Axis device."""
        adapter = MonoXAPIAdapter(device[CONF_HOST])
        system_information = await asyncio.wait_for(adapter.sysinfo(), 5)
        device.update(self.map_sysinfo_to_data(system_information))
        self._abort_if_unique_id_configured(updates={
            CONF_HOST: device[CONF_HOST],
        })
        self._abort_if_unique_id_configured(updates={
            CONF_HOST: device[CONF_SERIAL],
        })
        self.discovery_schema = {
            vol.Required(CONF_HOST, default=device[CONF_HOST]): str,
        }

        return await self.async_step_user()
