"""Handles the API for Home Assistant. Functionally, this class is the API for
the Home Assistant integration. It is responsible for handling the requests from
the Home Assistant integration and sending requests to the Mono X API pip package.
When the API receives a response from the Mono X API, it will parse the response
and send it to the Home Assistant integration. This class acts as an adapter for
the pip package and as a fascade to the Home Assistant integration."""
from __future__ import annotations
import logging
import time
from typing import Type, Union
from uart_wifi.communication import UartWifi
from uart_wifi.response import MonoXResponseType, MonoXStatus, MonoXSysInfo
from . import const
from .const import (
    ATTR_REMAINING_LAYERS,
    ATTR_TOTAL_TIME,
    ATTR_LOOKUP_TABLE,
    INTERNAL_FILE,
    TYPE_ML,
    UART_WIFI_PORT,
    API_VALUE_SPLIT_CHAR,
    API_TILDE,
    API_STATUS,
    API_SECONDS_ELAPSE,
)
from .errors import AnycubicException

# Logger for the class.
_LOGGER = logging.getLogger(__name__)


class MonoXAPIAdapter(UartWifi):
    """Class for MonoX API calls, Adapted to Home Assistant format."""

    def __init__(self, ip_address: str, port: int = UART_WIFI_PORT) -> None:
        """Construct our new MonoXAPI object.
        Note if the IP address containt :port, we will use that instead of
        the specified port. This facilitates better unit testing.

        Parameters:
        :ip_address: The IP address to target for communications.
        :port: The port for communications.
        """
        _LOGGER.info("Setting up connection")
        the_ip, url_port = _split_ip_and_port(ip_address, port)
        if url_port is not None and url_port != 0:
            port = int(url_port)
        super().__init__(the_ip, port)
        self.ip_address = the_ip
        self.port = port

    def get_current_status(
        self, convert_seconds: bool, no_extras: bool
    ) -> Union[MonoXStatus, dict] | bool:
        """Get the MonoX Status.  Waits for a maximum of 5 seconds.

        Parameters:
        :convert_seconds (bool): If this value is true, then we will convert the time
        provided to the API to seconds.  In the case of the MonoX, and the
        MonoX 4K, the time is provided in minutes. Therefore, by default,
        the API converts to seconds.  Since only the MonoX 6K is provided
        with a time in seconds, we must unconvert for this particular model.
        :no_extras (bool): If this value is true, then we will not pull the device
        extras.  Otherwise, we will not pull the device extras.

        Returns
        :returns (Union[MonoXStatus, dict] | bool): MonoXStatus, and a dict of extras,
        or a False."""
        try:
            _LOGGER.debug("Collecting Status")
            respone_stream = self.send_request("getstatus,\r\n")
            status: MonoXStatus = _find_response_of_type(
                response=respone_stream, expected_type=MonoXStatus
            )
            if status:
                extras = {}
                if not no_extras:
                    extras = _parse_extras(status, convert_seconds)
                return (status, extras)
        finally:
            # We close the telnet socket here because the device has limited
            # connections and broadcasts to all of them.  If the device has
            # open conections, the responses are slower and we may not
            # be the only ones using the device currently.
            self.telnet_socket.close()
        return (False, False)

    def sysinfo(self) -> MonoXSysInfo | bool:
        """Get the MonoX System Information.  Waits for a maximum of 5 seconds.
        In the event we do not return a valid response, we will return None.
         :returns ( MonoXSysInfo | bool): MonoXSysInfo or a false."""
        try:
            _LOGGER.debug("Collecting Sysinfo")
            response = self.send_request("sysinfo,\r\n")
            return _find_response_of_type(response=response, expected_type=MonoXSysInfo)
        except (OSError, RuntimeError) as ex:
            raise AnycubicException from ex
        finally:
            self.telnet_socket.close()


def _find_response_of_type(
    response: object, expected_type: Type(MonoXResponseType)
) -> MonoXResponseType | bool:
    """Mono X Responses come back as a single response, or multiple responses.  This is
    due to the nature of the telnet stream and the parsing provided by the API.  Since
    the API is an asynchronous and open telnet stream, all listeners receive the same
    messages from the printer.  Since all messages must be expected to arrive
    asynchronously, without any warning, out-of-order, and unexpectedly,
    we must parse the responses to determine if we received the correct response during
    the time spent listening to the port.  It is possible to receive full or partial
    messages intended for a different client, but we must determine if the message
    is the correct one.

    Parameters:
    :response: the response to check for a type
    :expected_type: the expected type of the response

    Returns:
    :returns: the first object matching the expected type, or False if no match is found."""
    if isinstance(response, expected_type):
        return response
    for item in response:
        if isinstance(item, expected_type):
            return item
    return False


def _parse_extras(raw_extras: dict, convert_seconds: bool) -> dict | None:
    """Parse the response from the getstatus command into extra attributes.

    Parameters:
    :raw_extras (dict): The raw response from the getstatus command.
    :convert_seconds (bool): If this value is true, then we will convert the time from
    monutes to seconds.

    Returns:
    :int: the status dictionary
    """
    extras: dict = {}
    if not hasattr(raw_extras, API_STATUS):
        # we received a response that does not have the status
        return extras
    if convert_seconds and hasattr(raw_extras, API_SECONDS_ELAPSE):
        # We need to convert the time from minutes to seconds.
        seconds_elapsed = int(raw_extras.seconds_elapse) / 60
        raw_extras.__dict__[API_SECONDS_ELAPSE] = seconds_elapsed

    # Loop through all the expected sensors and add them to the extras dict
    # pylint: disable=unused-variable
    for [api_sensor_name, hass_sensor_name, data_type, unit] in ATTR_LOOKUP_TABLE:
        # if the sensor data is present, parse the data
        if hasattr(raw_extras, api_sensor_name):
            raw_value = getattr(raw_extras, api_sensor_name)
            # parse the data based on the expected data type.
            try:
                match data_type:
                    case const.TYPE_FILE:
                        [external, internal] = raw_value.split(API_VALUE_SPLIT_CHAR)
                        extras[hass_sensor_name] = external
                        extras[INTERNAL_FILE] = internal
                    case const.TYPE_FLOAT:
                        extras[hass_sensor_name] = float(raw_value)
                    case const.TYPE_ML:
                        # get the raw numeric value of the sensor without the extra stuff
                        int_value: int = raw_value.replace(TYPE_ML, "").replace(
                            API_TILDE, ""
                        )
                        extras[hass_sensor_name] = int_value
                    case const.TYPE_INT:
                        extras[hass_sensor_name] = int(raw_value)
                    case const.TYPE_TIME:
                        extras[hass_sensor_name] = _seconds_to_hhmmss(raw_value)
                    case const.TYPE_STRING:
                        extras[hass_sensor_name] = raw_value
                    case _:
                        extras[hass_sensor_name] = raw_value
            except ValueError:
                # if the data is not in expected format, add it as a raw value
                extras[hass_sensor_name] = raw_value

        else:  # if the sensor data is not present, set a None value
            extras[hass_sensor_name] = None

    # Add the calculated Remaining Layers sensor
    if hasattr(raw_extras, "current_layer") and hasattr(raw_extras, "total_layers"):
        total = int(raw_extras.total_layers)
        current = int(raw_extras.current_layer)
        extras[ATTR_REMAINING_LAYERS] = int(total - current)
    else:
        # There is not enough info to calculate the remaining layers.
        extras[ATTR_REMAINING_LAYERS] = None

    # Add the calculated Seconds Elapsed sensor
    if hasattr(raw_extras, "seconds_elapse") and hasattr(
        raw_extras, "seconds_remaining"
    ):
        remain = int(raw_extras.seconds_remaining)
        elapsed = int(raw_extras.seconds_elapse)
        extras[ATTR_TOTAL_TIME] = _seconds_to_hhmmss(elapsed + remain)
    else:
        # There is not enough info to calculate the total time.
        extras[ATTR_TOTAL_TIME] = None

    return extras


def _seconds_to_hhmmss(raw_value):
    """Convert the raw seconds to the standard defined by
    Home assistant of form: h:min:s.
    :raw_value: the time to convert, in seconds."""
    gmt_time = time.gmtime(int(raw_value))
    hhmmss = time.strftime("%H:%M:%S", gmt_time)
    return hhmmss


def _split_ip_and_port(the_ip: str, port) -> tuple[str, int]:
    """Split the ip address from the port. If the port is provided in the
    IP address, then we use that.  Generally speaking this is unused,
    however it is valuable for testing as the fake_printer python object
    will select a random port for the fake printer to listen on. This
    method is only really used for testing.
    :the_ip: the IP address to use
    :port: The port to use.
    :returns: if the ip contains a semicolon, then the_ip's port
    will be returned otherwise we return the_ip and port
    """
    ipsplit = the_ip.split(":")
    if len(ipsplit) > 1:
        return ipsplit[0], int(ipsplit[1])
    return str(ipsplit[0]), int(port)
