"""Update coordinator"""
from datetime import timedelta
import logging
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from uart_wifi.errors import ConnectionException
from .errors import AnycubicException
from .const import (POLL_INTERVAL, ATTR_MANUFACTURER, DOMAIN, SUGGESTED_AREA)
from .mono_x_api_adapter_fascade import MonoXAPIAdapter

_LOGGER = logging.getLogger(__name__)


class AnycubicDataBridge(DataUpdateCoordinator):
    """The DataBridge is a coordinator that updates the data from the API.
    The purpose of the DataBridge is to provide a single point of access to
    the data from the API. This is done by using the built-in methods provided
    by the DataUpdateCoordinator. The DataBridge is responsible for outputting
    requests to the MonoX API and parsing the responses. The DataBridge is
    also responsible for handling the errors that may occur during the update
    process. """

    # Reported status extras is parsed from the status object and contains
    # extra state attributes for the sensor.
    _reported_status_extras: dict = {}

    # Certain MonoX devices measure elapsed time in seconds, while others measure
    # time in minutes.
    _measure_elapsed_in_seconds: bool = False

    # Mono X API Adapter provides limited access to the MonoX API and performs
    # minimal parsing on the data before it is passed to the data bridge.
    _monox: MonoXAPIAdapter

    # The config entry is held to provde Unique ID for the Device object.
    _config_entry: ConfigEntry

    # debounce counter accounts for the fact that the device has poor wifi connectivity.
    _debounce_counter: int = 0

    #When polling sensor status, also pull the device extras.
    _use_extras: bool = True

    def __init__(self, hass: HomeAssistant, monox: MonoXAPIAdapter,
                 config_entry: ConfigEntry) -> None:
        """Initialize the DataBridge.  Here we initialize the coordinator
        and set up the variables that will be used to update the data.
        :param hass: HomeAssistant the Home Assistant instance
        :param monox: MonoXAPIAdapter The MonoX API Adapter Fascade.
        :param config_entry: ConfigEntry The config entry for the device.
        """

        _LOGGER.info("Registering %s", monox.ip_address)
        super().__init__(
            hass,
            _LOGGER,
            name=f"anycubic-{monox.ip_address}",
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=POLL_INTERVAL),
        )
        self._config_entry = config_entry
        self._monox = monox
        self.data = {"status": "offline"}
        self._use_extras = True
        self._use_extras = not (hasattr(config_entry.options, "no_extras") or
                                config_entry.options.get("no_extras") is True)

    async def _async_update_data(self):
        """Update data via API. On the first sync this method will provide
        device information by establishing the system information, then provide
        deivce status.  On subsequent syncs, this method will provide device status.
        Failures to obtain data will result in the DataBridge being marked as
        offline. The sensor will respond to offline status as being unavailble."""
        try:
            [current_status, extras] = self._monox.get_current_status(
                use_seconds=self._measure_elapsed_in_seconds,
                use_extras=self._use_extras)
            if current_status:
                self._debounce_reset()
                if self._use_extras:
                    self._reported_status_extras.update(extras)
                else:
                    self._reported_status_extras = {}
                return current_status
        except (AnycubicException, ConnectionException,
                ConnectionRefusedError):
            # This is probably an API error, these devices have poor
            # wifi connectivity and are often offline.
            pass

        # Did not obtain a status, so we MAY be offline. The device
        # can be offline, or wifi is resetting. So we debounce for
        # three tries before reporting offline status.
        return self._offline_debounce()

    def _debounce_reset(self):
        """We received a message. Reset the debounce counter."""
        self._debounce_counter = 0

    def _offline_debounce(self):
        """Due to the intermittent connectivity issues, offline status
        requires debounce. Increment the debounce counter. If the counter
        is greater than zero, the device is considered offline. If the
        counter is greater than 3 then we raise an exception indicating to
        Home Assistant, the device is offline."""
        self._debounce_counter += 1
        if self._debounce_counter > 3:
            raise UpdateFailed("Failed to obtain status from device.")
        return self.data

    def get_last_status_extras(self):
        """"Return the last status extras for the sensor."""
        return self._reported_status_extras

    def get_printer(self):
        """Return the printer api for diagnostics."""
        return self._monox

    def set_use_extras(self, use_extras: bool):
        """Set the use_extras flag."""
        self._use_extras = use_extras

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        unique_id = cast(str, self._config_entry.unique_id)

        try:
            return DeviceInfo(identifiers={(DOMAIN, unique_id)},
                              manufacturer=ATTR_MANUFACTURER,
                              connections=[
                                  ("serial",
                                   self.config_entry.data["serial_number"])
                              ],
                              suggested_area=SUGGESTED_AREA,
                              sw_version=self.config_entry.data["sw_version"],
                              hw_version=self._monox.ip_address,
                              supported_features=self._monox.ip_address,
                              model=self.config_entry.data["model"],
                              name=ATTR_MANUFACTURER + " " +
                              self.config_entry.data["model"] + " " +
                              self.config_entry.data["serial_number"][-4:4])

        except AttributeError as ex:
            _LOGGER.debug(ex)
        return DeviceInfo(manufacturer=ATTR_MANUFACTURER)
