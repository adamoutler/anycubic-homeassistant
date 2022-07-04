"""Diagnostics support for Anycubic Wifi."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant

from .data_bridge import AnycubicDataBridge

from .const import DOMAIN

TO_REDACT = {CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE}


async def async_get_config_entry_diagnostics(
        hass: HomeAssistant, config_entry: ConfigEntry) -> dict:
    """Return diagnostics for a config entry."""
    bridge: AnycubicDataBridge = hass.data[DOMAIN][
        config_entry.entry_id]["bridge"]

    diagnostics_data = {
        "printer": bridge.monox.__dict__,
        "anycubic_data_bridge": bridge.__dict__
    }

    return diagnostics_data
