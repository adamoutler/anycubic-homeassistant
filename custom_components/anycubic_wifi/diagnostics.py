"""Diagnostics support for Anycubic Wifi."""
from __future__ import annotations
import json
import logging
from types import NoneType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .data_bridge import AnycubicDataBridge
from .const import DOMAIN

# Logger for the class
_LOGGER = logging.getLogger(__name__)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry. Here we dump everything
    we know about the config entry, integration, and the data bridge.
    This makes it easier to audit the data and debug issues."""
    bridge: AnycubicDataBridge = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entry_data = {}
    entry_data["config_entry"] = {
        "domain": config_entry.domain,
        "title": config_entry.title,
        "unique_id": safe_dump(config_entry.unique_id),
        "version": safe_dump(config_entry.version),
        "source": safe_dump(config_entry.source),
        "data": safe_dump(config_entry.data),
        "options": safe_dump(config_entry.options),
    }
    entry_data["data"] = safe_dump(config_entry.data)
    entry_data["options"] = safe_dump(config_entry.options)
    entry_data["extra_state_data"] = safe_dump(bridge.get_last_status_extras())
    data_bridge = safe_dump(bridge)
    data_bridge["data"] = safe_dump(bridge.data)
    diagnostics_data = {
        config_entry.entry_id: {
            "config_entry_data": safe_dump(entry_data),
            "hass data": safe_dump(hass.data[DOMAIN][config_entry.entry_id]),
            "anycubic_data_bridge": data_bridge,
        }
    }
    return diagnostics_data


def safe_dump(the_object):
    """Dump an object in a safe way. We want to ensure the object is in a
    proper format before we dump it. So we check if it's a raw object and
    simply return it.  If it is not a raw object,we check if it is possible
    to iterate as a dictionary.  If it is not possible, we make it into a
    dictionary and then iterate it.  All the values which can be
    json.dumps'd are added to a dictionary to be returned. Objects which
    cannot be json.dumps'd are toString'd and added to the dictionary."""
    _LOGGER.debug("Dumping object: %s %s", the_object, type(the_object))
    if isinstance(the_object, (int, float, str, bool, complex, NoneType)):
        return the_object
    elif str(the_object.__class__) in [
        "<class 'mappingproxy'>",
        "<class 'dict'>",
    ]:
        the_dict = the_object
    else:
        the_dict = the_object.__dict__
    new_dict = {}
    for key in the_dict:
        try:
            json.dumps(the_dict.get(key))
            new_dict.update({key: the_dict.get(key)})
        except (AttributeError, TypeError, OverflowError):
            new_dict.update({key: str(the_dict.get(key))})
    return new_dict
