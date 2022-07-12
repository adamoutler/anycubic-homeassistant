"""Diagnostics support for Anycubic Wifi."""
from __future__ import annotations
import json
import logging
from types import NoneType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from .data_bridge import AnycubicDataBridge
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

TO_REDACT = {CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE}


async def async_get_config_entry_diagnostics(
        hass: HomeAssistant, config_entry: ConfigEntry) -> dict:
    """Return diagnostics for a config entry."""
    bridge: AnycubicDataBridge = hass.data[DOMAIN][
        config_entry.entry_id]["coordinator"]

    diagnostic_object = {}
    entry = diagnostic_object["config_entry"] = {
        "domain": config_entry.domain,
        "title": config_entry.title,
        "unique_id": safe_dump(config_entry.unique_id),
        "version": safe_dump(config_entry.version),
        "source": safe_dump(config_entry.source),
        "data": safe_dump(config_entry.data),
        "options": safe_dump(config_entry.options)
    }
    entry["data"] = safe_dump(config_entry.data)
    entry["options"] = safe_dump(config_entry.options)
    entry["extra_state_data"] = safe_dump(bridge.get_last_status_extras())
    diagnostics_data = {
        config_entry.entry_id: {
            "config_entry_data": safe_dump(diagnostic_object),
            "hass data": safe_dump(hass.data[DOMAIN][config_entry.entry_id]),
            "anycubic_data_bridge": safe_dump(bridge)
        }
    }
    return diagnostics_data


def safe_dump(the_object):
    """Dump an object in a safe way."""
    _LOGGER.debug("Dumping object: %s %s", the_object, type(the_object))
    if isinstance(the_object, (int, float, str, bool, complex, NoneType)):
        return the_object
    elif str(the_object.__class__) in [
            "<class 'mappingproxy'>", "<class 'dict'>"
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
