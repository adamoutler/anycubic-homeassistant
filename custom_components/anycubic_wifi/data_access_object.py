"""Update coordinator"""
import asyncio
from datetime import timedelta
import logging
import time
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import callback

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from uart_wifi.response import MonoXSysInfo
from uart_wifi.response import MonoXStatus
from uart_wifi.errors import ConnectionException
from .errors import AnycubicException
from .const import (TYPE_INT, TYPE_STRING, TYPE_FLOAT, ATTR_MANUFACTURER,
                    TYPE_ML, ATTR_REMAINING_LAYERS, TYPE_TIME, ATTR_TOTAL_TIME,
                    DOMAIN, OFFLINE_STATUS, SUGGESTED_AREA,
                    TRANSLATION_ATTRIBUTES)
from .mono_x_api_adapter_fascade import MonoXAPIAdapter

_LOGGER = logging.getLogger(__name__)


class AnycubicDataBridge(DataUpdateCoordinator):
    """Coordinator for data updates"""
    monox: MonoXAPIAdapter
    reported_status: MonoXStatus = None
    reported_status_extras = None
    sysinfo: MonoXSysInfo = {}
    measure_elapsed_in_seconds = False
    entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, monox: MonoXAPIAdapter,
                 config_entry: ConfigEntry, interval: int) -> None:
        """Initialzie Update Cordinator"""
        super().__init__(
            hass,
            _LOGGER,
            name=f"anycubic-{config_entry.entry_id}",
            update_method=self.update,
            update_interval=timedelta(seconds=interval),
        )
        self.entry = config_entry
        self.monox = monox

    @callback
    async def update(self) -> None:
        """refresh data"""
        _LOGGER.debug("Update Called")
        await self._async_update_data()

    async def _async_update_data(self):
        """Update data via API."""
        _LOGGER.debug("Updating data")
        try:
            if (not self.sysinfo or not getattr(self.sysinfo, "model")):
                info = await asyncio.wait_for(self.monox.sysinfo(), 5)
                if hasattr(info, "model"):
                    self.sysinfo = info
                    self.measure_elapsed_in_seconds = "6K" in info.model
                else:
                    raise AnycubicException("offline")
            getstatus: MonoXStatus = await asyncio.wait_for(
                self.monox.getstatus(), 5)
            if getstatus is not None:
                self.reported_status = getstatus
                self.reported_status_extras = _parse_status_extras(
                    getstatus, self.measure_elapsed_in_seconds)
        except (AnycubicException, ConnectionException,
                ConnectionRefusedError) as ex:
            _LOGGER.warning('exception during update on %s: %s',
                            self.monox.ip_address, ex)
            self.reported_status = OFFLINE_STATUS
            self.reported_status_extras = {}
        if (self.reported_status is None
                or not hasattr(self.reported_status, "status")
                or not isinstance(self.reported_status, MonoXStatus)):
            self.reported_status = OFFLINE_STATUS
            self.reported_status_extras = {}
        _LOGGER.debug("Update complete")

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        unique_id = cast(str, self.entry.unique_id)

        try:
            return DeviceInfo(
                identifiers={(DOMAIN, unique_id)},
                manufacturer=ATTR_MANUFACTURER,
                connections=[("serial", self.coordinator.sysinfo.serial)],
                suggested_area=SUGGESTED_AREA,
                sw_version=self.coordinator.sysinfo.firmware,
                via_device=self.coordinator.sysinfo.wifi,
                model=self.coordinator.sysinfo.model,
                name=ATTR_MANUFACTURER + self.coordinator.sysinfo.model + " " +
                self.coordinator.sysinfo.serial[-4:4],
            )
        except AttributeError:
            pass
        return DeviceInfo(manufacturer=ATTR_MANUFACTURER)


def _seconds_to_hhmmss(raw_value):
    gmt_time = time.gmtime(int(raw_value))
    hhmmss = time.strftime('%H:%M:%S', gmt_time)
    return hhmmss


def _parse_status_extras(stat: MonoXStatus, use_seconds: bool) -> dict:
    """Handle status for Mono X getstatus message"""
    extras = {}

    if not stat or not stat.status:
        return
    if hasattr(stat, 'seconds_remaining') and use_seconds:
        remain = int(stat.seconds_remaining)
        stat.seconds_remaining = int(remain / 60)

    for [internal_attr, hass_attr, handling] in TRANSLATION_ATTRIBUTES:
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
