"""Handles the API for Home Assistant."""
from __future__ import annotations
import logging
import time
from typing import Type, Union
from uart_wifi.communication import UartWifi
from uart_wifi.response import MonoXResponseType, MonoXStatus, MonoXSysInfo
from .const import (ATTR_REMAINING_LAYERS, ATTR_TOTAL_TIME, ATTR_LOOKUP_TABLE,
                    TYPE_FLOAT, TYPE_INT, TYPE_ML, TYPE_STRING, TYPE_TIME,
                    UART_WIFI_PORT)
from .errors import AnycubicException

_LOGGER = logging.getLogger(__name__)


class MonoXAPIAdapter(UartWifi):
    """Class for MonoX API calls, Adapted to Home Assistant format."""

    def __init__(self, ip_address: str, port: int = UART_WIFI_PORT) -> None:
        """Construct our new MonoXAPI object.
        Note if the IP address containt :port, we will use that instead of
        the specified port. This facilitates better unit testing.
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
            self, use_seconds: bool,
            use_extras: bool) -> Union[MonoXStatus, dict] | bool:
        """Get the MonoX Status.  Waits for a maximum of 5 seconds.
        :returns: MonoXStatus or none."""
        try:
            _LOGGER.debug("Collecting Status")
            respone_stream = self.send_request("getstatus,\r\n")
            status: MonoXStatus = find_response_of_type(
                response=respone_stream, expected_type=MonoXStatus)
            if status:
                extras = {}
                if (use_extras):
                    extras = parse_extras(status, use_seconds)
                return (status, extras)
        finally:
            # We close the telnet socket here because the device has limited
            # connections and broadcasts to all of them.  If the device has
            # open conections, the responses are slower and we may not
            # be the only ones using the device currently.
            self.telnet_socket.close()
        return (False, False)

    def sysinfo(self) -> MonoXSysInfo | None:
        """Get the MonoX System Information.  Waits for a maximum of 5 seconds.
         :returns: MonoXSysInfo or none."""
        try:
            _LOGGER.debug("Collecting Sysinfo")
            response = self.send_request("sysinfo,\r\n")
            return find_response_of_type(response=response,
                                         expected_type=MonoXSysInfo)
        except (OSError, RuntimeError) as ex:
            raise AnycubicException from ex
        finally:
            self.telnet_socket.close()


def find_response_of_type(
    response: object, expected_type: Type(MonoXResponseType)
) -> MonoXResponseType | bool:
    """Mono X Responses come back as a single response, or multiple
    responses. Since they need to be parsed, this is where it happens.
    :response: the response to check for a type
    :expected_type: the expected type of the response
    :returns: the first object matching the type, or AnycubicMonoXAPILevel exception"""
    if isinstance(response, expected_type):
        return response
    for item in response:
        if isinstance(item, expected_type):
            return item
    return False


def parse_extras(stat: str, use_seconds: bool) -> dict | None:
    """Parse the response from the getstatus command.
    :response: the response to parse
    :returns: the status dictionary
    """
    extras: dict = {}
    if not stat or not hasattr(stat, "status"):
        return extras
    if hasattr(stat, 'seconds_remaining') and use_seconds:
        remain = int(stat.seconds_remaining)
        stat.seconds_remaining = int(remain / 60)

    for [internal_attr, hass_attr, handling] in ATTR_LOOKUP_TABLE:
        if hasattr(stat, internal_attr):
            raw_value = getattr(stat, internal_attr)
            #Can't wait for Python 3.10!
            if handling == TYPE_ML:
                raw_value = raw_value.replace(TYPE_ML, "").replace("~", "")
                extras[hass_attr] = int(raw_value)
            elif handling == TYPE_INT:
                extras[hass_attr] = int(raw_value)
            elif handling == TYPE_FLOAT:
                extras[hass_attr] = float(raw_value)
            elif handling == TYPE_TIME:
                extras[hass_attr] = _seconds_to_hhmmss(raw_value)
            elif handling == TYPE_STRING:
                extras[hass_attr] = raw_value
            else:
                extras[hass_attr] = raw_value
        else:
            extras[hass_attr] = None

    if hasattr(stat, 'current_layer') and hasattr(stat, 'total_layers'):
        total = int(stat.total_layers)
        current = int(stat.current_layer)
        extras[ATTR_REMAINING_LAYERS] = int(total - current)
    else:
        extras[ATTR_REMAINING_LAYERS] = None
    if hasattr(stat, 'seconds_elapse') and hasattr(stat, 'seconds_remaining'):
        remain = int(stat.seconds_remaining)
        elapsed = int(stat.seconds_elapse)
        extras[ATTR_TOTAL_TIME] = _seconds_to_hhmmss(elapsed - remain)
    else:
        extras[ATTR_TOTAL_TIME] = None

    return extras


def _seconds_to_hhmmss(raw_value):
    gmt_time = time.gmtime(int(raw_value))
    hhmmss = time.strftime('%H:%M:%S', gmt_time)
    return hhmmss


def _split_ip_and_port(the_ip: str, port) -> tuple[str, int]:
    """Split the ip address from the port.
    If the port is provided in the IP address,
    then we use that.
    :the_ip: the IP address to use
    :port: The port to use.
    :returns: if the ip contains a semicolon, then the_ip's port
    will be returned otherwise we return the_ip and port
    """
    ipsplit = the_ip.split(":")
    if len(ipsplit) > 1:
        return ipsplit[0], int(ipsplit[1])
    return str(ipsplit[0]), int(port)
