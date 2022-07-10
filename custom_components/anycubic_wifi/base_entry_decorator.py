"""Base classes for Anycubic Wifi entities. This class provides standard methods which are
    universal for all Anycubic Wifi entities. The base class provides access to the Anycubic
    data bridge, and by integrating with the Coordinator component, provides a standard way to
    handle the data update procedure."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .img.anycubic import AnycubicImages

from . import AnycubicDataBridge


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

    @property
    def device_info(self) -> DeviceInfo:
        """Retrieves the Device info, provided in the bridge."""
        return self.bridge.device_info

    @property
    def available(self) -> bool:
        """Return if entity is available. In the event the sensor is not
        available, the status is removed from the data bridge. This will
        cause the sensor to be unavailable, and the status will not be
        displayed in the UI. Removal of this check causes Home Assistant
        to display an error in logs when the sensor value is requested.

        If the sensor is reporting data, the sensor will be available.
        If the data bridge reports an error, the sensor will not be available.
        If the data bridge is not connected, the sensor will not be available.
        If the data bridge is connected, but the sensor is not reporting data,
        the sensor will not be available."""
        return hasattr(self.bridge.data, "status")

    @property
    def _attr_entity_picture(self):
        """Return the entity picture. If this is a MonoX, we return a picture
        of the Mono X style printer.  While slight variances exist in the X,
        4K, and 6K printers, the Entity Picture is 100x100 pixels, and variances
        in the models are not expected to be distinguishable. In the event
        another device is detected, the Entity Picture will not be displayed,
        thus resulting in a mdi:printer icon."""
        if ('model' in self.entry.data
                and str(self.entry.data["model"]).startswith("Photon Mono X")):
            return AnycubicImages.MONO_X_IMAGE
        else:
            return None

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes. This is a dictionary of
        attributes that will be added to the state attributes. This allows
        extra data to be provided to the user interface. It can be disabled
        in the event of too much data being delivered to the database, ie, if
        the printer is running rount-the-click for production, and not hobbiest
        purposes. It is configured in the Integrations UI via CONFIGURE button."""
        return self.bridge.get_last_status_extras()