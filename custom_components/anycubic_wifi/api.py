"""Handles the API for Home Assistant."""
from __future__ import annotations

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
        the_ip, the_port = get_split(ip_address, port)
        port = int(the_port)
        super().__init__(the_ip, port)
        self.ip_address = the_ip
        self.port = port

    def getstatus(self) -> MonoXStatus | None:
        """Get the MonoX Status"""
        try:
            return self.send_request("getstatus,\r\n")
        except OSError:
            raise AnycubicMonoXAPILevel from OSError

    def sysinfo(self) -> MonoXSysInfo | None:
        """Get the MonoX Status"""
        try:
            return self.send_request("sysinfo,\r\n")

        except OSError:
            raise AnycubicMonoXAPILevel from OSError



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
