"""Constants for the Anycubic 3D Printer integration."""

from homeassistant.const import Platform

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
TYPE_STRING = 'str'
TYPE_TIME = 'time'
TYPE_INT = 'int'
TYPE_ML = 'mL'
TYPE_FLOAT = "float"
ATTR_LOOKUP_TABLE = [["file", "file", TYPE_STRING],
                     ["current_layer", "Current Layers", TYPE_INT],
                     ["total_layers", "Total Layers", TYPE_INT],
                     ["layer_height", "Layer Height mm", TYPE_FLOAT],
                     ["percent_complete", '%' + " Complete", TYPE_INT],
                     ["seconds_elapse", "Time Elapsed", TYPE_TIME],
                     ["seconds_remaining", "Time Remaining", TYPE_TIME],
                     ["total_volume", "Print Volume mL", TYPE_ML],
                     ["mode", "Mode", TYPE_STRING],
                     ["unknown1", "unknown_1", TYPE_FLOAT],
                     ["unknown2", "unknown_2", TYPE_STRING]]
ATTR_REMAINING_LAYERS = "layers_remain_num"
ATTR_TOTAL_TIME = "total_print_time"
