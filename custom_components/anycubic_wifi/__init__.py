"""The Anycubic 3D Printer integration.
This integration utilizes a standard pull architecture to retrieve data from
your printer every const.POLL_INTERVAL and store it locally. It is then
rendered by the sensor entity.

The init.py file is the entry point for the integration. It is responsible for
creating the integration representation in hass.data.
"""
from __future__ import annotations
from datetime import timedelta
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .data_bridge import AnycubicDataBridge
from .mono_x_api_adapter_fascade import MonoXAPIAdapter
from .const import (DOMAIN, PLATFORMS, POLL_INTERVAL, ANYCUBIC_WIFI_PORT)

#Logger for the class.
_LOGGER = logging.getLogger(__name__)


# pylint: disable=unused-argument
async def async_setup(hass: HomeAssistant, processed: ConfigType) -> bool:
    """At initialization, this method is called.  This is where we establish
        a point in Home Assistant for our data to be located.  We elect to use
        the standard hass.data[.const.DOMAIN] dictionary to store our data. A
        component could use this to pass true/false or throw a
        ConfigEntryAuthFailed, ConfigEntryNotReady or other exception to
        indicate that the entry is unable to initialize.
    :param hass: HomeAssistant api reference to all of the Home Assistant data.
    :param processed: A dictionary of items which have already been setup by
        config_entries.py. This can be used to provide an order to the setup of
        the integration.
    :returns: True if the setup was successful. If we cannot access the data,
        an exception is thrown."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Anycubic Printer from a config entry. This is where individual
        entries are setup. Start by setting up data location and polling time
        deltas, and then establish the data bridge to the 3D printer. The first
        data refresh action occurs, then the sensors are setup.
    :param hass: HomeAssistant api reference to all of the Home Assistant data.
    :param entry: The config entry to setup.
    :returns: True if the setup was successful. This will always be successful
        barring problems with Home Assistant or the underlying APIs. In the
        event a communication-type excepiton occurs, Home Assistant will
        declare this entry unable to be setup, requiring a reconfiguration or
        restart to bring us back online."""
    entry_location = hass.data[DOMAIN].setdefault(entry.entry_id, {})
    poll_delta = timedelta(seconds=POLL_INTERVAL)
    entry_location[CONF_SCAN_INTERVAL] = poll_delta

    bridge = get_new_data_bridge(hass, entry)
    await bridge.async_config_entry_first_refresh()
    entry_location["coordinator"] = bridge

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


def get_new_data_bridge(hass, entry) -> AnycubicDataBridge:
    """Get the data bridge for the given config entry.  The data bridge is
        a Home Assistant coordinator which is responsible for managing the
        data collection and preparation for the sensor entities. The bridge
        follows the Python bridge design pattern and is the action component
        for the Coordinator component.
    :param hass: HomeAssistant api reference to all of the Home Assistant data.
    :param entry: The config entry of item being setup.
    :returns: The data bridge for the given config entry.
    """

    api = MonoXAPIAdapter(entry.data[CONF_HOST], ANYCUBIC_WIFI_PORT)
    bridge = AnycubicDataBridge(hass, api, entry)
    return bridge


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """When an entry changes, the update_listener is called.  This is where
        live configuration updates are handled. The procedure for this
        particular integration is to simply refresh the entity. Refresh
        occurs by removing the existing entity and creating a new one.
    :param hass: HomeAssistant api reference to all of the Home Assistant data.
    :param entry: The config entry of item being setup."""
    hass.data[DOMAIN].pop(entry.entry_id)
    await async_setup_entry(hass, entry)
    await hass.config_entries.async_reload(entry.entry_id)


def get_existing_bridge(hass: HomeAssistant,
                        entry: ConfigEntry) -> AnycubicDataBridge:
    """Get the data bridge for the given config entry.  The data bridge is
        a Home Assistant coordinator which is responsible for managing the
        data collection and preparation for the sensor entities. The bridge
        follows the Python bridge design pattern and is the action component
        for the Coordinator component.
    :param hass: HomeAssistant api reference to all of the Home Assistant data.
    :param entry: The config entry of item being setup.
    :returns: The data bridge for the given config entry."""
    bridge: AnycubicDataBridge = hass.data[DOMAIN][
        entry.entry_id]["coordinator"]
    return bridge


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the provided config entry. This is a sad procedure. We will clean
        up the mess we made, and Home Assistant will remove the assigned entries.
    :param hass: HomeAssistant api reference to all of the Home Assistant data.
    :param entry: The config entry of item being setup. """
    if unload_ok := await hass.config_entries.async_unload_platforms(
            entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
