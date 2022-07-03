"""Base classes for MonoX entities."""

import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from uart_wifi.response import MonoXStatus

from .const import OFFLINE_STATUS

from . import AnycubicDataBridge


# https://github.com/home-assistant/core/blob/dev/homeassistant/components/octoprint/sensor.py#L92
class AnycubicEntityBaseDecorator(CoordinatorEntity[AnycubicDataBridge],
                                  Entity):
    """Base common to all MonoX entities."""

    def __init__(self, entry: ConfigEntry,
                 dao: AnycubicDataBridge) -> None:
        """Initialize the base MonoX entity object.
        :entry: the configuration data.
        :coordinator: the processing and storage of updates.
        """
        self.entry = entry
        self.dao = dao
        self._attr_unique_id = self.entry.entry_id
        super().__init__(dao)

    async def async_added_to_hass(self) -> None:
        """Subscribe device events."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, "unload",
                                     self.update_callback))

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if (self.dao is None
                or not isinstance(self.dao.reported_status, MonoXStatus)):
            return False
        return self.dao.reported_status.status is not OFFLINE_STATUS

    @callback
    async def update_callback(self) -> None:
        """Update the entities state."""
        self.async_write_ha_state()

    def set_attr_time(self, key: str, value: int) -> None:
        """Handle state attributes"""
        self._attr_extra_state_attributes[key] = str(
            datetime.timedelta(seconds=value))
