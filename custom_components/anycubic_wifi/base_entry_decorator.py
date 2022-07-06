"""Base classes for MonoX entities."""

import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo


from . import AnycubicDataBridge


# https://github.com/home-assistant/core/blob/dev/homeassistant/components/octoprint/sensor.py#L92
class AnycubicEntityBaseDecorator(CoordinatorEntity[AnycubicDataBridge]):
    """Base common to all MonoX entities."""

    def __init__(self, entry: ConfigEntry, bridge: AnycubicDataBridge) -> None:
        """Initialize the base MonoX entity object.
        :entry: the configuration data.
        :coordinator: the processing and storage of updates.
        """
        self.entry = entry
        self.bridge = bridge
        self._attr_unique_id = self.entry.entry_id
        super().__init__(bridge)

    async def async_added_to_hass(self) -> None:
        """Subscribe device events."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, "unload",
                                     self.update_callback))

    @callback
    async def update_callback(self) -> None:
        """Update the entities state."""
        self.async_write_ha_state()

    def set_attr_time(self, key: str, value: int) -> None:
        """Handle state attributes"""
        self._attr_extra_state_attributes[key] = str(
            datetime.timedelta(seconds=value))

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        return self.bridge.device_info

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
