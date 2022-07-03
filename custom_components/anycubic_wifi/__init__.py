"""The Anycubic 3D Printer integration."""
from __future__ import annotations
from datetime import timedelta
import logging
import slugify
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import (CONF_HOST, CONF_MONITORED_CONDITIONS,
                                 CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from uart_wifi.errors import ConnectionException
from .data_access_object import AnycubicDataBridge
from .mono_x_api_adapter_fascade import MonoXAPIAdapter
from .const import ANYCUBIC_3D_PRINTER_NAME, DOMAIN, PLATFORMS, POLL_INTERVAL

# For your initial PR, limit it to 1 platform.
_LOGGER = logging.getLogger(__name__)
DEFAULT_NAME = ANYCUBIC_3D_PRINTER_NAME
SENSOR_TYPES = ["Concise"]

SENSOR_SCHEMA = vol.Schema({
    vol.Optional(CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)):
    vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME):
    cv.string,
})


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
            entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the device."""
    if DOMAIN not in config:
        return True
    domain_config = config[DOMAIN]
    for conf in domain_config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={
                    CONF_HOST: conf[CONF_HOST],
                    CONF_PORT: conf[CONF_PORT],
                },
            ))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Anycubic Printer from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][CONF_SCAN_INTERVAL] = timedelta(seconds=POLL_INTERVAL)

    host = entry.data[CONF_HOST]
    port = 6000
    if ":" in host:
        [host, port] = entry.data[CONF_HOST].split(":")

    api = MonoXAPIAdapter(host, port)
    dao = AnycubicDataBridge(hass, api, entry, POLL_INTERVAL)
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": dao,
    }

    await dao.update()
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


def get_monox_info(host: str, port: int = 6000) -> None:
    """Gather information from the device, given the IP address"""
    api = MonoXAPIAdapter(host, port)
    try:
        sysinfo = api.sysinfo()
    except ConnectionException:
        return
    return sysinfo
