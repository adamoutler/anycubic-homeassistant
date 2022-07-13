"""Platform for sensor integration."""

# The sensor sits on the data bridge/coordinator.
# Device Info < Data Bridge > adapter fascade > uart-wifi pip > 3D Printer
#                    \/
#               sensor entity

from __future__ import annotations
from datetime import timedelta
from typing import Any

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from .data_bridge import AnycubicDataBridge
from .base_entry_decorator import AnycubicEntityBaseDecorator

from .const import (ATTR_LOOKUP_TABLE, DOMAIN, OPT_HIDE_EXTRA_SENSORS,
                    PRINTER_ICON, POLL_INTERVAL)

SCAN_INTERVAL = timedelta(seconds=POLL_INTERVAL)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up the platform from config_entry. We use the config entry to get the
    IP address of the printer, and then create a data bridge to the printer. the
    data bridge will in turn initialize the API adapter, then be integrated with
    the base entity decorator and the sensor itself. The sensor will be added to
    the list of entities to be managed by Home Assistant."""
    coordinator: AnycubicDataBridge = hass.data[DOMAIN][
        entry.entry_id]["coordinator"]

    @callback
    async def async_add_sensor(sensor: Any, name: str, unit: str) -> None:
        """Add sensor from Anycubic device into the Home Assistant entity
        registry."""

        async_add_entities([
            MonoXSensor(bridge=coordinator,
                        hass=hass,
                        entry=entry,
                        native_update=sensor,
                        name=name,
                        unit=unit)
        ])

    @callback
    async def async_add_extra_sensor(sensor: Any, name: str,
                                     unit: str) -> None:
        """Add sensor from Anycubic device into the Home Assistant entity
        registry."""

        async_add_entities([
            MonoXExtraSensor(bridge=coordinator,
                             hass=hass,
                             entry=entry,
                             native_update=sensor,
                             name=name,
                             unit=unit)
        ])

    # extra_sensors = entry.options["extra_sensors"]
    # if extra_sensors:
    #     for (data, name, type) in ATTR_LOOKUP_TABLE:
    #         await async_add_sensor(coordinator.data[name])
    # else:
    await async_add_sensor("status", "status", "")
    if not entry.options.get(OPT_HIDE_EXTRA_SENSORS):
        # pylint: disable=unused-variable
        for [unused, sensor, datatype, unit] in ATTR_LOOKUP_TABLE:
            await async_add_extra_sensor(sensor, unused, unit)


class MonoXSensor(AnycubicEntityBaseDecorator, SensorEntity):
    """A sensor with extra data. This sensor is a wrapper around the Anycubic
    EntityBaseDecorator. It provides the methods required by Home Assistant to
    handle outputting the sensor data into the user interface.

    It includes SensorEntity methods to implement standard sensor functionality.
    """

    _attr_icon = PRINTER_ICON
    _attr_device_class = "3D Printer"
    should_poll = True
    async_update_interval = SCAN_INTERVAL

    def __init__(self, bridge: AnycubicDataBridge, hass: HomeAssistant,
                 entry: ConfigEntry, native_update: str, name: str,
                 unit: str) -> None:
        """Initialize the sensor.
        :coordinator: The data retrieval and storage for this sensor.
        :hass: A reference to Home Assistant.
        :entry: This device's configuration data.
        """
        super().__init__(entry=entry, bridge=bridge, name=name)
        self.hass = hass
        self.native_update = native_update
        self._attr_native_unit_of_measurement = unit
        if not self.name:
            self._attr_name = self.device_info[CONF_NAME] + " " + name

    @property
    def native_value(self):
        """Return sensor state. Since this value is not processed, and delivered
        directly to the sensor, it is considered a native value.  This can be
        overridden by home assistant user to provide a custom value."""

        return (self.bridge.data.status)

    async def async_update(self):
        """Update the sensor."""
        return self.native_value

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        return self.bridge.is_online()


class MonoXExtraSensor(MonoXSensor):

    def __init__(self, bridge: AnycubicDataBridge, hass: HomeAssistant,
                 entry: ConfigEntry, native_update: str, name: str,
                 unit: str) -> None:
        super().__init__(bridge=bridge,
                         hass=hass,
                         entry=entry,
                         native_update=native_update,
                         name=name,
                         unit=unit)

    @property
    def native_value(self):
        """Return sensor state. Since this value is not processed, and delivered
        directly to the sensor, it is considered a native value.  This can be
        overridden by home assistant user to provide a custom value."""
        try:
            return self.bridge.get_last_status_extras()[self.native_update]
        except KeyError:
            return None

    async def async_update(self):
        """Update the sensor."""
        return self.native_value

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        return self.native_value
