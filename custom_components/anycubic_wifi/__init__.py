"""The Anycubic 3D Printer integration.
This integration utilizes a standard pull architecture to retrieve data from
your printer every const.POLL_INTERVAL and store it locally. It is then
rendered by the sensor entity.

The init.py file is the entry point for the integration. It is responsible for
creating the integration representation in hass.data.
"""
# pylint disable=anomalous-backslash-in-string

# The overall project layout is as follows:
#             Init Config Entry
#                    \/
#  Device Info < Data Bridge > adapter fascade > uart-wifi pip > 3D Printer
#                    \/
#               sensor entity

from __future__ import annotations
from datetime import timedelta
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.device_registry import DeviceRegistry

from .data_bridge import AnycubicDataBridge
from .adapter_fascade import MonoXAPIAdapter
from .const import (DOMAIN, PLATFORMS, POLL_INTERVAL, ANYCUBIC_WIFI_PORT)

#Logger for the class.
_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle migration of a previous version config entry.
    A config entry created under a previous version must go through the
    integration setup again so we can properly retrieve the needed data
    elements. Force this by removing the entry and triggering a new flow.
    """
    # Remove the entry which will invoke the callback to delete the app.
    hass.async_create_task(hass.config_entries.async_remove(entry.entry_id))
    # only create new flow if there isn't a pending one for SmartThings.
    if not hass.config_entries.flow.async_progress_by_handler(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}))
    return True


# pylint: disable=unused-argument
async def async_setup(hass: HomeAssistant, processed: ConfigType) -> bool:
    """UNUSED.
    This method isn't used, nor is it needed, but it's in "the minimum"
    example, so it feels wrong to not have it.

    :param hass: HomeAssistant api reference to all of the Home Assistant data.
    :param processed: A dictionary of items which have already been setup by
        config_entries.py. This can be used to provide an order to the setup of
        the integration.
    :returns: True... always."""
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
    #setup the basic datastructure in hass.

    entry_location = hass.data[DOMAIN].setdefault(entry.entry_id, {})

    #setup the data bridge.
    poll_delta = timedelta(seconds=POLL_INTERVAL)
    entry_location[CONF_SCAN_INTERVAL] = poll_delta
    bridge = get_new_data_bridge(hass, entry)
    await bridge.async_config_entry_first_refresh()
    entry_location["coordinator"] = bridge

    #Setup options listener.
    entry.async_on_unload(entry.add_update_listener(opt_update_listener))

    #Setup the sensors.
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


async def opt_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """When an entry changes, the update_listener is called.  This is where
        live configuration updates are handled. The procedure for this
        particular integration is to simply refresh the entity. Refresh occurs
        by removing the existing device from the registry, thereby taking all
        the device entities with the old device and removing them. Then the
        device is added back to the registry during async_setup_entry. This
        will trigger a new entity setup.
    :param hass: HomeAssistant api reference to all of the Home Assistant data.
    :param entry: The config entry of item being setup."""
    #find and remove the device from the registry
    registry: DeviceRegistry = hass.data['device_registry']
    device = registry.async_get_device(identifiers=[(DOMAIN, entry.unique_id)])
    registry.async_remove_device(device.id)
    #setup the device again
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
