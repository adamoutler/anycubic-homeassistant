"""Handles the API for Home Assistant."""
from __future__ import annotations
from typing import Iterable

from uart_wifi.communication import UartWifi
from uart_wifi.response import MonoXStatus, MonoXSysInfo
from .errors import AnycubicMonoXAPILevel
from .const import UART_WIFI_PORT


class MonoXAPI(UartWifi):
    """Class for MonoX API calls, Adapted to Home Assistant format."""

    def __init__(self, ip_address: str, port: int = UART_WIFI_PORT) -> None:
        """Construct our new MonoXAPI object.
        Note if the IP address containt :port, we will use that instead of
        the specified port. This facilitates better unit testing.
        :ip_address: The IP address to target for communications.
        :port: The port for communications.
        """
        the_ip, url_port = get_split(ip_address, port)
        if url_port is not None and url_port != 0:
            port = int(url_port)
        super().__init__(the_ip, port)
        self.ip_address = the_ip
        self.port = port

    def getstatus(self) -> MonoXStatus | None:
        """Get the MonoX Status"""
        try:
            response = self.send_request("getstatus,\r\n")
            if response is None:
                return None
            if isinstance(response, MonoXStatus):
                return response
            for item in response:
                if isinstance(item, MonoXStatus):
                    adjust_based_on_time_deltav(item)
                    return item

        except OSError:
            raise AnycubicMonoXAPILevel from OSError

    def sysinfo(self) -> MonoXSysInfo | None:
        """Get the MonoX Status"""
        try:
            response = self.send_request("sysinfo,\r\n")
            for item in response:
                if isinstance(item, MonoXSysInfo):
                    return item
            if isinstance(response, MonoXSysInfo):
                return response
        except OSError:
            raise AnycubicMonoXAPILevel from OSError


def adjust_based_on_time_deltav(response: MonoXStatus) -> None:
    """ "The MonoX/Monox4k use minutes to record elapsed time.
        The MonoX 6k uses sec. This method adjusts and adapts.
    : response : The Status Message"""
    if response.status == "print":
        elapsed = int(response.seconds_elapse)
        remain = int(response.seconds_remaining)
        total = elapsed + remain
        percent = elapsed / total * 100
        claimed_percent = int(response.percent_complete)
        variance_delta = percent / claimed_percent
        if  variance_delta >= 1.1:
            # this is a printer which records elapsed in seconds.
            response.seconds_elapse = response.seconds_elapse / 60


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
