"""Handles the API for Home Assistant."""
from __future__ import annotations
from typing import Iterable

from uart_wifi.communication import UartWifi
from uart_wifi.response import MonoXStatus, MonoXSysInfo, MonoXResponseType
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
        the_ip, the_port = get_split(ip_address, port)
        port = int(the_port)
        super().__init__(the_ip, port)
        self.ip_address = the_ip
        self.port = port

    def getstatus(self) -> MonoXStatus | None:
        """Get the MonoX Status"""
        try:
            responses = self.send_request("getstatus,\r\n")
            for response in responses:
                if isinstance(response, MonoXStatus):
                    adjust_based_on_time_deltav(response)
                    return response

        except OSError:
            raise AnycubicMonoXAPILevel from OSError

    def sysinfo(self) -> MonoXSysInfo | None:
        """Get the MonoX Status"""
        try:
            return self.send_request("sysinfo,\r\n")

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
        if not 0.8 <= variance_delta <= 1.2:
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
