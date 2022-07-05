"""Constants for the Anycubic 3D Printer integration."""

from homeassistant.const import Platform
from uart_wifi.response import MonoXStatus

DOMAIN = "anycubic_wifi"
PLATFORMS: list[Platform] = [Platform.SENSOR]
ATTR_MANUFACTURER = "Anycubic"
SUPPORTED_MACS = ["28:6d:cd"]
ANYCUBIC_3D_PRINTER_NAME = "Anycubic 3D Printer"
NAME = ATTR_MANUFACTURER
UART_WIFI_PORT = 6000
CONF_EVENTS = "events"
CONF_MODEL = "model"
PRINTER_ICON = "mdi:printer-3d"
DEFAULT_STATE = "offline"
CONF_SERIAL = "serial_number"
SW_VERSION = "sw_version"
SUGGESTED_AREA = "Garage"
DEFAULT_EVENTS = True
POLL_INTERVAL = 10  # seconds
ANYCUBIC_WIFI_PORT = 6000
CONFIG_FLOW_VERSION = 1
UART_WIFI_PROTOCOL = "Anycubic Uart Wifi Protocol"
TYPE_STRING = 'str'
TYPE_TIME = 'time'
TYPE_INT = 'int'
TYPE_ML = 'mL'
TYPE_FLOAT = "float"
TRANSLATION_ATTRIBUTES = [["file", "file", TYPE_STRING],
                          ["total_layers", "total_layer_num", TYPE_INT],
                          ["percent_complete", "complete", TYPE_INT],
                          ["current_layer", "current_layer_num", TYPE_INT],
                          ["seconds_elapse", "elapsed", TYPE_TIME],
                          ["seconds_remaining", "remaining", TYPE_TIME],
                          ["total_volume", "print_vol_mL", TYPE_ML],
                          ["mode", "mode", TYPE_STRING],
                          ["unknown1", "unknown_1", TYPE_FLOAT],
                          ["layer_height", "layer_height", TYPE_FLOAT],
                          ["unknown2", "unknown_2", TYPE_STRING]]
ATTR_REMAINING_LAYERS = "layers_remain_num"
ATTR_TOTAL_TIME = "total_print_time"
OFFLINE_STATUS = MonoXStatus(["getstatus", "offline", "end"])
