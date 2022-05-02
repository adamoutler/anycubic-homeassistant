"""Utility class to update mono x configuration"""
from uart_wifi.response import MonoXSysInfo
from uart_wifi.errors import ConnectionException
from homeassistant.const import CONF_HOST, CONF_NAME

from .api import MonoXAPI
from .const import (
    CONF_MODEL,
    CONF_SERIAL,
    SW_VERSION,
)


async def get_monox_info(host: str, data: dict, port: int = 6000) -> None:
    """Gather information from the device, given the IP address"""
    api = MonoXAPI(host, port)
    try:
        sysinfo = api.sysinfo()
    except ConnectionException:
        return

    if isinstance(sysinfo, MonoXSysInfo):
        data[CONF_HOST] = host
        map_sysinfo_to_data(sysinfo, data)


def map_sysinfo_to_data(sysinfo: MonoXSysInfo, data: dict) -> None:
    """map the sysInfo result to a dictionary"""
    data[SW_VERSION] = sysinfo.firmware
    data[CONF_MODEL] = sysinfo.model
    data[CONF_NAME] = sysinfo.model
    data[CONF_SERIAL] = sysinfo.serial
