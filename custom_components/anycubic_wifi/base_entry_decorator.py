"""Base classes for Anycubic Wifi entities. This class provides standard
    methods which are universal for all Anycubic Wifi entities. The base class
    provides access to the Anycubic data bridge, and by integrating with the
    Coordinator component, provides a standard way to handle the data update
    procedure."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.const import CONF_HOST, CONF_MODEL
from .const import (
    OPT_HIDE_EXTRA_SENSORS,
    OPT_HIDE_IP,
    OPT_NO_EXTRA_DATA,
    OPT_USE_PICTURE,
)
from .img.anycubic import AnycubicImages
from . import AnycubicDataBridge


class AnycubicEntityBaseDecorator(
    CoordinatorEntity[AnycubicDataBridge], Entity
):
    """Base common to all MonoX entities."""

    def __init__(
        self,
        entry: ConfigEntry,
        bridge: AnycubicDataBridge,
        sensor_generic_name: str,
    ) -> None:
        """Initialize the base MonoX entity object.
        :param entry: the configuration data.
        :param coordinator: the processing and storage of updates.
        :param sensor_generic_name: the name of the sensor EG status or layers.
        """
        self.entry = entry
        # Make it shorter to prevent elipses when displayed in UI.
        # Instead of "Photon Mono X 6K Status", use "Mono X 6K Status"
        # https://developers.home-assistant.io/blog/2022/07/10/entity_naming/
        model = entry.data[CONF_MODEL].replace("Photon ", "")
        self.sensor_attr_name = sensor_generic_name
        self._attr_name = model + " " + sensor_generic_name
        self._attr_unique_id = self.entry.entry_id + sensor_generic_name
        self.bridge = bridge
        super().__init__(bridge)

    @property
    def device_info(self) -> DeviceInfo:
        """Retrieves the Device info, provided in the bridge. This is
        provided in the Base entity so that it does not need to be inherited
        by ell other entities. The common device info links all the sensors
        to the same device, thus providing a consistent device name and
        manufacturer.
        :return: the device info."""
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
        the sensor will not be available.
        :return: True if the sensor is available, False otherwise."""
        return hasattr(self.bridge.data, "status")

    @property
    def _attr_assumed_state(self) -> bool:
        """Return if entity is assumed state. In the event the sensor is not
        available, the status is assumed as unchanged until the sensor is
        determined to be offline or available. This will cause the sensor to
        continue operation even with the device's poor wifi connection, and
        will cause the assumed status to be displayed in the UI
        :return: True if the sensor is assumed state, False otherwise."""
        return self.bridge.assumed_state

    @property
    def _attr_entity_picture(self) -> str:
        """Return the entity picture. If this is a MonoX, we return a picture
        of the Mono X style printer.  While slight variances exist in the X,
        4K, and 6K printers, the Entity Picture is 100x100 pixels, and
        variances in the models are not expected to be distinguishable. In the
        event another device is detected, the Entity Picture will not be
        displayed, thus resulting in a mdi:printer icon.
        :return: the entity picture if the user has opted to use it."""
        # If the user selected the option..
        if self.entry.options[OPT_USE_PICTURE]:
            # If we have a relevant picture, return it.
            if "model" in self.entry.data and str(
                self.entry.data["model"]
            ).startswith("Photon Mono X"):
                return AnycubicImages.MONO_X_IMAGE
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes. These are hidden if the user has not
        selected  to display a single sensor, or if the extras are disabled.
        The Host name will be placed into the extras unless the user has
        disabled the option. The user is in control of these settings via
        options.
        :return: the state attributes unless otherwise blocked."""
        extras = self.bridge.get_last_status_extras()
        # If user option no extras or hide extras is set, then we dont report.
        if (
            self.entry.options[OPT_NO_EXTRA_DATA]
            or not self.entry.options[OPT_HIDE_EXTRA_SENSORS]
        ):
            extras = {}

        # if user option Hide IP is set, then we hide the IP as well.
        if not self.entry.options[OPT_HIDE_IP]:
            extras.update({CONF_HOST: self.entry.data[CONF_HOST]})
        return extras
