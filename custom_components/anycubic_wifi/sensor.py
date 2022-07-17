"""Platform for sensor integration."""

# The sensor sits on the data bridge/coordinator.
# Device Info < Data Bridge > adapter fascade > uart-wifi pip > 3D Printer
#                    \/
#               sensor entity

from __future__ import annotations
from datetime import timedelta

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from .data_bridge import AnycubicDataBridge
from .base_entry_decorator import AnycubicEntityBaseDecorator

from .const import (
    ATTR_LOOKUP_TABLE,
    DOMAIN,
    OPT_HIDE_EXTRA_SENSORS,
    PRINTER_ICON,
    POLL_INTERVAL,
)

# The time interval between scans
SCAN_INTERVAL = timedelta(seconds=POLL_INTERVAL)

# Logger for this class.
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform from config_entry. We use the config entry to get
    the IP address of the printer, and then create a data bridge to the
    printer. the data bridge will in turn initialize the API adapter, then be
    integrated with the base entity decorator and the sensor itself. The
    sensor will be added to the list of entities to be managed by Home
    Assistant."""
    coordinator: AnycubicDataBridge = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    @callback
    async def async_add_sensor(name: str, unit: str) -> None:
        """Add sensor from Anycubic device into the Home Assistant entity
        registry."""

        async_add_entities(
            [
                MonoXSensor(
                    bridge=coordinator,
                    hass=hass,
                    entry=entry,
                    native_update=name,
                    name=name,
                    unit=unit,
                )
            ]
        )

    async def async_add_extra_sensor(
        sensor: str,
        name: str,
        unit: str,
    ) -> None:
        """Add sensor from Anycubic device into the Home Assistant entity
        registry. This is used for the extra sensors which are sub-messages
        of the primary message received by the device.  These sensors literally
        do not exist when the printer is in "stopped" or "finished" state.
        :param sensor: The queriable extra-data portion of the sensor.
        :param name: The name of the sensor.
        :param unit: The unit of the sensor."""

        async_add_entities(
            [
                MonoXExtraSensor(
                    bridge=coordinator,
                    hass=hass,
                    entry=entry,
                    native_update=sensor,
                    name=name,
                    unit=unit,
                )
            ]
        )

    await async_add_sensor(name="status", unit="")
    if not entry.options.get(OPT_HIDE_EXTRA_SENSORS):
        # pylint: disable=unused-variable
        for [sensor, name, unused, unit] in ATTR_LOOKUP_TABLE:
            await async_add_extra_sensor(sensor, name, unit)


class MonoXSensor(AnycubicEntityBaseDecorator, SensorEntity):
    """A sensor with extra data. This sensor is a wrapper around the Anycubic
    EntityBaseDecorator. It provides the methods required by Home Assistant to
    handle outputting the sensor data into the user interface. It also provides
    the methods required by the AnycubicEntityBaseDecorator to handle the data
    retrieval and storage.

    It includes SensorEntity methods to implement standard sensor
    functionality.
    """

    _attr_icon = PRINTER_ICON
    _attr_device_class = "3D Printer"
    should_poll = True
    async_update_interval = SCAN_INTERVAL

    def __init__(
        self,
        bridge: AnycubicDataBridge,
        hass: HomeAssistant,
        entry: ConfigEntry,
        native_update: str,
        name: str,
        unit: str,
    ) -> None:
        """Initialize the sensor.
        :coordinator: The data retrieval and storage for this sensor.
        :hass: A reference to Home Assistant.
        :entry: This device's configuration data.
        """
        super().__init__(entry=entry, bridge=bridge, name=name)
        self.hass = hass
        self.native_update = native_update
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        """Return sensor state. Since this value is not processed, and delivered
        directly to the sensor, it is considered a native value.  This can be
        overridden by home assistant user to provide a custom value."""
        return self.bridge.data.status

    async def async_update(self):
        """Update the sensor value when requested by Home Assistant."""
        return self.native_value


class MonoXExtraSensor(MonoXSensor):
    """A sensor with extra data. This sensor is a wrapper around the Anycubic
    EntityBaseDecorator. It provides the methods required by Home Assistant to
    handle outputting the sensor data into the user interface. It includes
    SensorEntity methods to implement standard sensor functionality."""

    def __init__(
        self,
        bridge: AnycubicDataBridge,
        hass: HomeAssistant,
        entry: ConfigEntry,
        native_update: str,
        name: str,
        unit: str,
    ) -> None:
        """Initialize the sensor. We override the name of the sensor to be the
        name of the attribute. This is done to make it easier to identify the
        sensor in the UI."""
        super().__init__(
            bridge=bridge,
            hass=hass,
            entry=entry,
            native_update=native_update,
            name=name,
            unit=unit,
        )

    @property
    def native_value(self):
        """Return sensor state. Since this value is not processed, and delivered
        directly to the sensor, it is considered a native value.  This can be
        overridden by home assistant user to provide a custom value."""
        extras = self.bridge.get_last_status_extras()
        if self.sensor_attr_name in extras:
            return extras[self.sensor_attr_name]
        return None

    @property
    def available(self) -> bool:
        """Return if the sensor is available. We override this method to make
        the state of the sensor apparent to Home Assistant so that it can be
        used in the UI. When the device is not printing, we get no information
        on these sensors, so they become unavailable. If self.native_value is
        None, we return False to indicate that the sensor is unavailable."""
        return self.sensor_attr_name is not None
