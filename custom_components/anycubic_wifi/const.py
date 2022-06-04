"""Constants for the Anycubic 3D Printer integration."""

from homeassistant.const import Platform


DOMAIN = "anycubic_wifi"
ATTR_MANUFACTURER = "Anycubic"
UART_WIFI_PORT = 6000
CONF_EVENTS = "events"
CONF_MODEL = "model"
ANYCUBIC_3D_PRINTER_NAME = "Anycubic 3D Printer"
SUPPORTED_MACS = ["28:6d:cd"]
BASED_ON = "axis"
PRINTER_ICON = "mdi:printer-3d"
DEFAULT_STATE = "offline"
CONF_SERIAL = "serial_number"
SW_VERSION = "sw_version"
DEFAULT_EVENTS = True
POLL_INTERVAL = 60  # seconds
PLATFORMS = [Platform.SENSOR]
CONFIG_FLOW_VERSION = 1
