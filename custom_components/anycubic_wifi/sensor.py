"""Platform for sensor integration."""
from __future__ import annotations
from datetime import timedelta
import logging

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.components.sensor import SensorEntity

from .data_bridge import AnycubicDataBridge

from .base_entry_decorator import AnycubicEntityBaseDecorator
from .const import (
    CONF_MODEL,
    DOMAIN,
    PRINTER_ICON,
    POLL_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=POLL_INTERVAL)


async def async_setup(entry: config_entries.ConfigEntry) -> None:
    """The setup method"""
    _LOGGER.debug(entry)


async def async_setup_entry(hass: HomeAssistant,
                            entry: config_entries.ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up the platform from config_entry."""
    coordinator: AnycubicDataBridge = hass.data[DOMAIN][
        entry.entry_id]["coordinator"]

    @callback
    async def async_add_sensor() -> None:
        """Add sensor from Anycubic device."""
        the_sensor = MonoXSensor(bridge=coordinator, hass=hass, entry=entry)
        async_add_entities([the_sensor])
        entry.async_on_unload(
            entry.add_update_listener(the_sensor.async_update))

    await async_add_sensor()
    return


class MonoXSensor(SensorEntity, AnycubicEntityBaseDecorator, RestoreEntity):
    """A sensor with extra data."""

    # _attr_changed_by = None
    _attr_icon = PRINTER_ICON
    _attr_device_class = "3D Printer"
    should_poll = True

    def __init__(self, bridge: AnycubicDataBridge, hass: HomeAssistant,
                 entry: ConfigEntry) -> None:
        """Initialize the sensor.
        :coordinator: The data retrieval and storage for this sensor.
        :hass: A reference to Home Assistant.
        :entry: This device's configuration data.
        """
        super().__init__(entry=entry, bridge=bridge)
        self.entry = entry
        self.hass = hass

        if not self.name:
            self._attr_name = entry.data[CONF_MODEL]

        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN,
                                                          entry.unique_id)})

    @property
    def extra_state_attributes(self):
        return self.bridge.reported_status_extras

    @property
    def native_value(self):
        """Return sensor state."""
        return self.coordinator.reported_status.status

    async def async_added_to_hass(self):
        """Set up previous values when the device is added to Home Assiatant.
        This occurs at Home Assistant reboot, or during device configuration.
        """

        last_state = await self.async_get_last_state()

        if (last_state is None or last_state is not dict):
            return
        if "state" in last_state:
            self.state = last_state.state
        last_extras = await self.async_get_last_extra_data()
        if last_extras is not None and "last_extras" in last_state:
            self.coordinator.reported_status_extras = last_extras

    @callback
    async def update_callback(self) -> None:
        """Update the sensor's state.
        """
        self.hass.add_job(self.async_update_ha_state(self.async_update))
