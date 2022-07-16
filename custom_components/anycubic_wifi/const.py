"""Constants for the Anycubic 3D Printer integration."""

from homeassistant.const import Platform
from homeassistant.const import (
    VOLUME_MILLILITERS,
    LENGTH_MILLIMETERS,
    PERCENTAGE,
    TIME_HOURS,
    TIME_MINUTES,
    TIME_SECONDS,
)
from uart_wifi.communication import MonoXStatus

DOMAIN = "anycubic_wifi"
PLATFORMS: list[Platform] = [Platform.SENSOR]
ATTR_MANUFACTURER = "Anycubic"
SUPPORTED_MACS = ["28:6d:cd"]
ANYCUBIC_3D_PRINTER_NAME = "Anycubic 3D Printer"
NAME = ATTR_MANUFACTURER
UART_WIFI_PORT = 6000
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
CONF_DHCP = "dhcp"
TYPE_STRING = "str"
TYPE_TIME = "time"
TYPE_INT = "int"
TYPE_ML = "mL"
TYPE_FLOAT = "float"
TYPE_FILE = "file"
INTERNAL_FILE = "Internal File Name"
STATUS_OFFLINE = MonoXStatus(["getstatus", "offline"])
ATTR_REMAINING_LAYERS = "Layers Remaining"
ATTR_TOTAL_TIME = "Total Print Time"
UNIT_HMS = TIME_HOURS + ":" + TIME_MINUTES + ":" + TIME_SECONDS
# The following are the keys for the lookup table
# [sensor value name, display name, data type, unit]
ATTR_LOOKUP_TABLE = [
    ["file", "file", TYPE_FILE, ""],
    ["current_layer", "Current Layer", TYPE_INT, ""],
    ["total_layers", "Total Layers", TYPE_INT, ""],
    ["layer_height", "Layer Height", TYPE_FLOAT, LENGTH_MILLIMETERS],
    ["percent_complete", "%" + " Complete", TYPE_INT, PERCENTAGE],
    ["seconds_elapse", "Time Elapsed", TYPE_TIME, UNIT_HMS],
    ["seconds_remaining", "Time Remaining", TYPE_TIME, UNIT_HMS],
    ["total_volume", "Print Volume", TYPE_ML, VOLUME_MILLILITERS],
    ["mode", "Mode", TYPE_STRING, ""],  # Mode is always UV
    ["unknown1", "unknown_1", TYPE_FLOAT, ""],
    ["unknown2", "unknown_2", TYPE_STRING, ""],
    [ATTR_REMAINING_LAYERS, ATTR_REMAINING_LAYERS, TYPE_TIME, ""],
    [ATTR_TOTAL_TIME, ATTR_TOTAL_TIME, TYPE_TIME, UNIT_HMS],
]
CONVERT_SECONDS_MODEL = "Mono X 6K"
OPT_NO_EXTRA_DATA = "no_extras"
OPT_HIDE_IP = "hide_ip"
OPT_HIDE_EXTRA_SENSORS = "hide_extra_sensors"
OPT_USE_PICTURE = "use_picture"
API_MODEL = "model"
API_SERIAL = "serial"
API_FIRMWARE = "firmware"
API_STATUS= "status"
API_SECONDS_ELAPSE= "seconds_elapse"
API_TILDE= "~"
API_VALUE_SPLIT_CHAR="/"