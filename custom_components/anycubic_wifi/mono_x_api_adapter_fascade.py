"""Handles the API for Home Assistant."""
from __future__ import annotations
import logging
from typing import Type
from uart_wifi.communication import UartWifi
from uart_wifi.response import MonoXResponseType, MonoXStatus, MonoXSysInfo
from .errors import AnycubicMonoXAPILevel
from .const import UART_WIFI_PORT

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
        the_ip, url_port = get_split(ip_address, port)
        if url_port is not None and url_port != 0:
            port = int(url_port)
        super().__init__(the_ip, port)
        self.ip_address = the_ip
        self.port = port

    async def getstatus(self) -> MonoXStatus | None:
        """Get the MonoX Status
        :returns: MonoXStatus or none."""
        try:
            _LOGGER.debug("Collecting Status")
            response = self.send_request("getstatus,\r\n")
            self.telnet_socket.close()
            return parse_response_stream(response=response,
                                         expected_type=MonoXStatus)
        except OSError:
            raise AnycubicMonoXAPILevel from OSError

    async def sysinfo(self) -> MonoXSysInfo | None:
        """Get the MonoX Status
         :returns: MonoXSysInfo or none."""
        try:
            _LOGGER.debug("Collecting Sysinfo")
            response = self.send_request("sysinfo,\r\n")
            self.telnet_socket.close()
            return parse_response_stream(response=response,
                                         expected_type=MonoXSysInfo)
        except OSError:
            raise AnycubicMonoXAPILevel from OSError


def parse_response_stream(
    response: object, expected_type: Type(MonoXResponseType)
) -> MonoXResponseType | None:
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
    return None


def get_split(the_ip: str, port) -> tuple[str, int]:
    """Split the ip address from the port.
    If the port is provided in the IP address,
    then we use that.
    :the_ip: the IP address to use
    :port: The port to use.
    """
    ipsplit = the_ip.split(":")
    if len(ipsplit) > 1:
        return ipsplit[0], ipsplit[1]
    return str(ipsplit[0]), int(port)
