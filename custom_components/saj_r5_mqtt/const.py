"""Constants for the SAJ R5 MQTT integration."""

from __future__ import annotations

from datetime import timedelta
from enum import Enum, StrEnum
import logging

DOMAIN = "saj_r5_mqtt"
BRAND = "SAJ"
MANUFACTURER = "SAJ Electric"
MODEL = "R5 series inverter"
MODEL_SHORT = "R5"

# Device type constants (from register 0x8F00)
DEVICE_TYPE_SUNUNO_1MPPT = 0x0011
DEVICE_TYPE_SUNUNO_2MPPT = 0x0012
DEVICE_TYPE_SUNTRIO_3PHASE = 0x0021
DEVICE_TYPE_SUNTRIO_3PHASE_V2 = 0x0023  # Alternative three-phase variant (found in field)

# Configuration constants
CONF_SERIAL_NUMBER = "serial_number"
CONF_SCAN_INTERVAL_REALTIME_DATA = "scan_interval_realtime_data"
CONF_SCAN_INTERVAL_INVERTER_DATA = "scan_interval_inverter_data"
CONF_SCAN_INTERVAL_CONFIG_DATA = "scan_interval_config_data"
CONF_ENABLE_SERIAL_NUMBER_PREFIX = "enable_serial_number_prefix"
CONF_ENABLE_ACCURATE_REALTIME_POWER_DATA = "enable_accurate_realtime_power_data"
CONF_ENABLE_MQTT_DEBUG = "enable_mqtt_debug"

# Service constants
SERVICE_READ_REGISTER = "read_register"
SERVICE_WRITE_REGISTER = "write_register"
SERVICE_REFRESH_INVERTER_DATA = "refresh_inverter_data"
SERVICE_REFRESH_CONFIG_DATA = "refresh_config_data"

# Attribute constants
ATTR_CONFIG_ENTRY = "config_entry"
ATTR_REGISTER = "register"
ATTR_REGISTER_FORMAT = "register_format"
ATTR_REGISTER_SIZE = "register_size"
ATTR_REGISTER_VALUE = "register_value"

# Modbus constants
MODBUS_MAX_REGISTERS_PER_QUERY = (
    0x64  # Absolute max is 123 (0x7b) registers per MQTT packet request (do not exceed)
)
MODBUS_DEVICE_ADDRESS = 0x01
MODBUS_READ_REQUEST = 0x03
MODBUS_WRITE_REQUEST = 0x06

# R5 Modbus registers
MODBUS_REG_POWER_LIMIT = 0x801F
MODBUS_REG_TIME = 0x8020  # 4 words: yyyyMMddHHmmsszz

# Mqtt constants
MQTT_READY = "MQTT_READY"
MQTT_QOS = 2
MQTT_RETAIN = False
MQTT_ENCODING = None
MQTT_DATA_TRANSMISSION = "data_transmission"
MQTT_DATA_TRANSMISSION_RSP = "data_transmission_rsp"
MQTT_DATA_TRANSMISSION_TIMEOUT = 10
MQTT_WAIT_SLEEP_TIME = 0.05  # time in s

# Default constants
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

LOGGER = logging.getLogger(__package__)


class WorkingMode(Enum):
    """R5 Working mode (register 0x0100)."""

    WAIT = 0x01
    NORMAL = 0x02  # on grid run mode
    FAULT = 0x03
    UPDATE = 0x04


class PVState(StrEnum):
    """PV state."""

    PRODUCING = "producing"
    STANDBY = "standby"
