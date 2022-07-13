"""Update coordinator"""
from datetime import timedelta
import logging
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import (CONF_MODEL, ATTR_SW_VERSION, CONF_HOST)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from uart_wifi.errors import ConnectionException

from .errors import AnycubicException
from .const import (CONF_SERIAL, POLL_INTERVAL, ATTR_MANUFACTURER, DOMAIN, STATUS_OFFLINE,
                    SUGGESTED_AREA, OPT_NO_EXTRA_DATA, CONVERT_SECONDS_MODEL)
from .adapter_fascade import MonoXAPIAdapter

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
    _convert_seconds: bool = False

    # Mono X API Adapter provides limited access to the MonoX API and performs
    # minimal parsing on the data before it is passed to the data bridge.
    _monox: MonoXAPIAdapter

    # The config entry is held to provde Unique ID for the Device object.
    _config_entry: ConfigEntry

    # The data is held to provide the debounce function to the system so
    # we don't spam the logs with offline messages.
    _connection_retries: int = 0

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
        self._convert_seconds = CONVERT_SECONDS_MODEL in config_entry.data[
            CONF_MODEL]

    async def _async_update_data(self):
        """Update data via API. On the first sync this method will provide
        device information by establishing the system information, then provide
        deivce status.  On subsequent syncs, this method will provide device status.
        Failures to obtain data will result in the DataBridge being marked as
        offline. The sensor will respond to offline status as being unavailble."""
        try:
            [current_status, extras] = self._monox.get_current_status(
                convert_seconds=self._convert_seconds,
                no_extras=self._config_entry.options[OPT_NO_EXTRA_DATA])
            if current_status:
                # We have connection, so we can reset the connection retries.
                self._connection_retries = 0
                if self._config_entry.options[OPT_NO_EXTRA_DATA]:
                    #no extras status.
                    self._maybe_add_host_to_extras()
                else:
                    #update the data source status.
                    self._reported_status_extras.update(extras)
                    #add the host to the extras if it's not already there.
                    self._maybe_add_host_to_extras()

                return current_status
        except (AnycubicException, ConnectionException,
                ConnectionRefusedError):
            # This is probably a connectivity error, these devices have poor
            # wifi connectivity and are often offline.
            pass

        return self.debounce_failure_response()

    def debounce_failure_response(self):
        """Debounce the data bridge.  These devices have very poor wifi
        connectivity. We don't want to spam the logs with offline messages.
        Instead, we want to debounce the failure response and only report
        problems when the device is not responsive for a while. I've
        observed 250 failures in a 16 hour period, polling at a 10 second
        interval with the wifi router located within 5 feet of the device.
        """
        self._connection_retries += 1
        if self._connection_retries > 5:
            raise UpdateFailed("Failed to obtain status from device.")
        #Report the offline status.
        return STATUS_OFFLINE


    def _maybe_add_host_to_extras(self):
        """If the extra data does not already contain the host, add it.
        This is used to provide the host to the sensor extras."""
        if not self._config_entry.options[OPT_NO_EXTRA_DATA] and not hasattr(
                self._reported_status_extras, CONF_HOST):
            self._reported_status_extras.update(
                {CONF_HOST: self._monox.ip_address})

    def get_last_status_extras(self):
        """"provide a public method to give the last status extras for the sensor."""
        return self._reported_status_extras

    def get_printer(self):
        """Return the printer api for diagnostics."""
        return self._monox


# pylint: disable=anomalous-backslash-in-string

    @property
    def device_info(self) -> DeviceInfo:
        """Device info. This implements all the required attributes for the
        device object. The device object is used by Home Assistant to provide
        information about the device in the UI and in the Device Registry.
        """
        unique_id = cast(str, self._config_entry.unique_id)

        try:
            return DeviceInfo(
                identifiers={(DOMAIN, unique_id)},
                manufacturer=ATTR_MANUFACTURER,
                connections=[(CONF_SERIAL, self.config_entry.data[CONF_SERIAL])
                             ],
                suggested_area=SUGGESTED_AREA,
                sw_version=self.config_entry.data[ATTR_SW_VERSION],
                supported_features=self._monox.ip_address,
                model=self.config_entry.data[CONF_MODEL],
                name=ATTR_MANUFACTURER + " " +
                self.config_entry.data[CONF_MODEL] + " " +
                self.config_entry.data[CONF_SERIAL][-4:4],
            )

        except AttributeError as ex:
            _LOGGER.debug(ex)
        return DeviceInfo(manufacturer=ATTR_MANUFACTURER)
