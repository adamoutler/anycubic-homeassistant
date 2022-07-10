"""Handles the API for Home Assistant."""
from __future__ import annotations
import logging
import time
from typing import Type, Union
from uart_wifi.communication import UartWifi
from uart_wifi.response import MonoXResponseType, MonoXStatus, MonoXSysInfo
from . import const
from .const import (ATTR_REMAINING_LAYERS, ATTR_TOTAL_TIME, ATTR_LOOKUP_TABLE, INTERNAL_FILE,
                     TYPE_ML,
                    UART_WIFI_PORT)
from .errors import AnycubicException

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
            self, convert_seconds: bool,
            no_extras: bool) -> Union[MonoXStatus, dict] | bool:
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
                response=respone_stream, expected_type=MonoXStatus)
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
            return _find_response_of_type(response=response,
                                         expected_type=MonoXSysInfo)
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
    :returns: the first object matching the type, or AnycubicMonoXAPILevel exception"""
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
    if not hasattr(raw_extras, "status"):
        return extras
    if hasattr(raw_extras, 'seconds_remaining') and convert_seconds:
        remain = int(raw_extras.seconds_remaining)
        raw_extras.seconds_remaining = int(remain / 60)

    for [internal_attr, hass_attr, handling] in ATTR_LOOKUP_TABLE:
        if hasattr(raw_extras, internal_attr):
            raw_value = getattr(raw_extras, internal_attr)
            match handling:
                case const.TYPE_FILE:
                    [external,internal]= raw_value.split("/")
                    extras[hass_attr] = external
                    extras[INTERNAL_FILE]= internal
                case const.TYPE_FLOAT :
                    extras[hass_attr] = float(raw_value)
                case const.TYPE_ML :
                    raw_value = raw_value.replace(TYPE_ML, "").replace("~", "")
                    extras[hass_attr] = int(raw_value)
                case const.TYPE_INT :
                    extras[hass_attr] = int(raw_value)
                case const.TYPE_TIME:
                    extras[hass_attr] = _seconds_to_hhmmss(raw_value)
                case const.TYPE_STRING:
                    extras[hass_attr] = raw_value
                case _:
                    extras[hass_attr] = raw_value
        else:
            extras[hass_attr] = None

    if hasattr(raw_extras, 'current_layer') and hasattr(raw_extras, 'total_layers'):
        total = int(raw_extras.total_layers)
        current = int(raw_extras.current_layer)
        extras[ATTR_REMAINING_LAYERS] = int(total - current)
    else:
        extras[ATTR_REMAINING_LAYERS] = None
    if hasattr(raw_extras, 'seconds_elapse') and hasattr(raw_extras, 'seconds_remaining'):
        remain = int(raw_extras.seconds_remaining)
        elapsed = int(raw_extras.seconds_elapse)
        extras[ATTR_TOTAL_TIME] = _seconds_to_hhmmss(elapsed - remain)
    else:
        extras[ATTR_TOTAL_TIME] = None

    return extras


def _seconds_to_hhmmss(raw_value):
    """Convert the raw seconds to a string of the form HH:MM:SS.
    :raw_value: the time to convert, in seconds."""
    gmt_time = time.gmtime(int(raw_value))
    hhmmss = time.strftime('%H:%M:%S', gmt_time)
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
