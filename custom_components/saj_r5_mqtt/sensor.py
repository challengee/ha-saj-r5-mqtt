"""Sensors for the SAJ R5 MQTT integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_TYPE_SUNTRIO_3PHASE,
    DEVICE_TYPE_SUNTRIO_3PHASE_V2,
    LOGGER,
    PVState,
    WorkingMode,
)
from .coordinator import SajR5MqttDataCoordinator
from .entity import SajR5MqttEntity, SajR5MqttEntityDescription, get_entity_description
from .types import SajR5MqttConfigEntry


@dataclass(frozen=True, kw_only=True)
class SajR5MqttSensorEntityDescription(
    SensorEntityDescription, SajR5MqttEntityDescription
):
    """A class that describes SAJ R5 MQTT sensor entities."""


# fmt: off

# Realtime data sensors (register range 0x0100-0x0137)
SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS: tuple[SajR5MqttSensorEntityDescription, ...] = (
    # Working Mode (0x0100)
    SajR5MqttSensorEntityDescription(key="inverter_working_mode", entity_registry_enabled_default=True, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x0, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: WorkingMode(x).name if x in [e.value for e in WorkingMode] else f"UNKNOWN_{x}"),

    # PV1 Data (0x0107-0x0109)
    SajR5MqttSensorEntityDescription(key="pv1_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0xE, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajR5MqttSensorEntityDescription(key="pv1_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x10, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajR5MqttSensorEntityDescription(key="pv1_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x12, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),

    # PV2 Data (0x010A-0x010C)
    SajR5MqttSensorEntityDescription(key="pv2_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0x14, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajR5MqttSensorEntityDescription(key="pv2_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x16, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajR5MqttSensorEntityDescription(key="pv2_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x18, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),

    # PV3 Data (0x010D-0x010F) - for some models only
    SajR5MqttSensorEntityDescription(key="pv3_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0x1A, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajR5MqttSensorEntityDescription(key="pv3_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x1C, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajR5MqttSensorEntityDescription(key="pv3_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x1E, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),

    # Bus Voltage (0x0110)
    SajR5MqttSensorEntityDescription(key="bus_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0x20, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),

    # Inverter Temperature (0x0111)
    SajR5MqttSensorEntityDescription(key="inverter_temperature", entity_registry_enabled_default=True, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfTemperature.CELSIUS, modbus_register_offset=0x22, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),

    # GFCI (0x0112)
    SajR5MqttSensorEntityDescription(key="gfci", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE, modbus_register_offset=0x24, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),

    # Total Power (0x0113)
    SajR5MqttSensorEntityDescription(key="total_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x26, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),

    # Reactive Power (0x0114)
    SajR5MqttSensorEntityDescription(key="reactive_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.REACTIVE_POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement="var", modbus_register_offset=0x28, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),

    # Power Factor (0x0115)
    SajR5MqttSensorEntityDescription(key="power_factor", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER_FACTOR, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=0x2A, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),

    # L1 Phase Data (0x0116-0x011B)
    SajR5MqttSensorEntityDescription(key="l1_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0x2C, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l1_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x2E, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l1_frequency", entity_registry_enabled_default=True, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfFrequency.HERTZ, modbus_register_offset=0x30, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l1_dci", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x32, modbus_register_data_type=">h", modbus_register_scale=0.001, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l1_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x34, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l1_power_factor", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER_FACTOR, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=0x36, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),

    # L2 Phase Data (0x011C-0x0121) - Three-phase models only
    SajR5MqttSensorEntityDescription(key="l2_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0x38, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l2_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x3A, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l2_frequency", entity_registry_enabled_default=True, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfFrequency.HERTZ, modbus_register_offset=0x3C, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l2_dci", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x3E, modbus_register_data_type=">h", modbus_register_scale=0.001, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l2_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x40, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l2_power_factor", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER_FACTOR, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=0x42, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),

    # L3 Phase Data (0x0122-0x0127) - Three-phase models only
    SajR5MqttSensorEntityDescription(key="l3_voltage", entity_registry_enabled_default=True, device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricPotential.VOLT, modbus_register_offset=0x44, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l3_current", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x46, modbus_register_data_type=">h", modbus_register_scale=0.01, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l3_frequency", entity_registry_enabled_default=True, device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfFrequency.HERTZ, modbus_register_offset=0x48, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l3_dci", entity_registry_enabled_default=True, device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfElectricCurrent.AMPERE, modbus_register_offset=0x4A, modbus_register_data_type=">h", modbus_register_scale=0.001, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l3_power", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=UnitOfPower.WATT, modbus_register_offset=0x4C, modbus_register_data_type=">h", modbus_register_scale=1.0, value_fn=None),
    SajR5MqttSensorEntityDescription(key="l3_power_factor", entity_registry_enabled_default=True, device_class=SensorDeviceClass.POWER_FACTOR, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=0x4E, modbus_register_data_type=">h", modbus_register_scale=0.1, value_fn=None),

    # ISO Sensors (0x0128-0x012B)
    SajR5MqttSensorEntityDescription(key="iso1", entity_registry_enabled_default=True, device_class=None, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement="kΩ", modbus_register_offset=0x50, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),
    SajR5MqttSensorEntityDescription(key="iso2", entity_registry_enabled_default=True, device_class=None, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement="kΩ", modbus_register_offset=0x52, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),
    SajR5MqttSensorEntityDescription(key="iso3", entity_registry_enabled_default=True, device_class=None, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement="kΩ", modbus_register_offset=0x54, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),
    SajR5MqttSensorEntityDescription(key="iso4", entity_registry_enabled_default=True, device_class=None, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement="kΩ", modbus_register_offset=0x56, modbus_register_data_type=">H", modbus_register_scale=1.0, value_fn=None),

    # Energy Statistics
    # Today Energy (0x012C)
    SajR5MqttSensorEntityDescription(key="today_pv_energy", entity_registry_enabled_default=True, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, modbus_register_offset=0x58, modbus_register_data_type=">H", modbus_register_scale=0.01, value_fn=None),

    # Month Energy (0x012D-0x012E) - 32-bit
    SajR5MqttSensorEntityDescription(key="month_pv_energy", entity_registry_enabled_default=True, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, modbus_register_offset=0x5A, modbus_register_data_type=">I", modbus_register_scale=0.01, value_fn=None),

    # Year Energy (0x012F-0x0130) - 32-bit
    SajR5MqttSensorEntityDescription(key="year_pv_energy", entity_registry_enabled_default=True, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, modbus_register_offset=0x5E, modbus_register_data_type=">I", modbus_register_scale=0.01, value_fn=None),

    # Total Energy (0x0131-0x0132) - 32-bit
    SajR5MqttSensorEntityDescription(key="total_pv_energy", entity_registry_enabled_default=True, device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR, modbus_register_offset=0x62, modbus_register_data_type=">I", modbus_register_scale=0.01, value_fn=None),

    # Working Hours
    # Today Hours (0x0133)
    SajR5MqttSensorEntityDescription(key="today_hours", entity_registry_enabled_default=True, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfTime.HOURS, modbus_register_offset=0x66, modbus_register_data_type=">H", modbus_register_scale=0.1, value_fn=None),

    # Total Hours (0x0134-0x0135) - 32-bit
    SajR5MqttSensorEntityDescription(key="total_hours", entity_registry_enabled_default=True, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfTime.HOURS, modbus_register_offset=0x68, modbus_register_data_type=">I", modbus_register_scale=0.1, value_fn=None),

    # Error Count (0x0136)
    SajR5MqttSensorEntityDescription(key="error_count", entity_registry_enabled_default=True, device_class=None, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement="errors", modbus_register_offset=0x6C, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
)

# Inverter data sensors (register range 0x8F00-0x8F1C)
SAJ_INVERTER_DATA_SENSOR_DESCRIPTIONS: tuple[SajR5MqttSensorEntityDescription, ...] = (
    # Device Type (0x8F00)
    SajR5MqttSensorEntityDescription(key="device_type", entity_registry_enabled_default=True, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x0, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: f"0x{x:04X}"),

    # Sub Type (0x8F01)
    SajR5MqttSensorEntityDescription(key="sub_type", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x2, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: f"0x{x:04X}"),

    # Protocol Version (0x8F02)
    SajR5MqttSensorEntityDescription(key="protocol_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x4, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: f"{(x >> 8) & 0xFF}.{x & 0xFF}"),

    # Serial Number (0x8F03-0x8F0C) - 10 words, 20 bytes
    SajR5MqttSensorEntityDescription(key="serial_number", entity_registry_enabled_default=True, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x6, modbus_register_data_type="20s", modbus_register_scale=None, value_fn=lambda x: x.rstrip("\x00")),

    # Product Code (0x8F0D-0x8F16) - 10 words, 20 bytes
    SajR5MqttSensorEntityDescription(key="product_code", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x1A, modbus_register_data_type="20s", modbus_register_scale=None, value_fn=lambda x: x.rstrip("\x00")),

    # Software Versions
    SajR5MqttSensorEntityDescription(key="display_software_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x2E, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: f"{(x >> 8) & 0xFF}.{x & 0xFF}"),
    SajR5MqttSensorEntityDescription(key="master_ctrl_software_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x30, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: f"{(x >> 8) & 0xFF}.{x & 0xFF}"),
    SajR5MqttSensorEntityDescription(key="slave_ctrl_software_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x32, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: f"{(x >> 8) & 0xFF}.{x & 0xFF}"),

    # Hardware Versions
    SajR5MqttSensorEntityDescription(key="display_hardware_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x34, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: f"{(x >> 8) & 0xFF}.{x & 0xFF}"),
    SajR5MqttSensorEntityDescription(key="ctrl_hardware_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x36, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: f"{(x >> 8) & 0xFF}.{x & 0xFF}"),
    SajR5MqttSensorEntityDescription(key="power_hardware_version", entity_registry_enabled_default=False, device_class=None, state_class=None, native_unit_of_measurement=None, modbus_register_offset=0x38, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=lambda x: f"{(x >> 8) & 0xFF}.{x & 0xFF}"),
)

# Config data sensors (register range 0x801F-0x8023)
SAJ_CONFIG_DATA_SENSOR_DESCRIPTIONS: tuple[SajR5MqttSensorEntityDescription, ...] = (
    # Power Limit (0x801F)
    SajR5MqttSensorEntityDescription(key="power_limit", entity_registry_enabled_default=True, device_class=None, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE, modbus_register_offset=0x0, modbus_register_data_type=">H", modbus_register_scale=None, value_fn=None),
)

# fmt: on


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SajR5MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SAJ R5 MQTT sensors."""
    saj_data = config_entry.runtime_data

    # Get device type for conditional sensor creation
    device_type = None
    if saj_data.coordinator_inverter_data and saj_data.coordinator_inverter_data.data:
        # Read device type from first word of inverter data (0x8F00)
        device_type_bytes = saj_data.coordinator_inverter_data.data[0:2]
        device_type = int.from_bytes(device_type_bytes, byteorder="big")
        LOGGER.debug(f"Detected device type: 0x{device_type:04X}")

    is_three_phase = device_type in (DEVICE_TYPE_SUNTRIO_3PHASE, DEVICE_TYPE_SUNTRIO_3PHASE_V2)

    # Create realtime sensors
    sensors: list[SensorEntity] = []
    for description in SAJ_REALTIME_DATA_SENSOR_DESCRIPTIONS:
        # Skip L2/L3 sensors if not three-phase
        if not is_three_phase and description.key.startswith(("l2_", "l3_")):
            continue

        # TODO: Add logic to skip PV3 sensors for single MPPT models
        # For now, we'll create all PV3 sensors

        sensors.append(
            SajR5MqttSensorEntity(
                coordinator=saj_data.coordinator_realtime_data,
                description=description,
            )
        )

    # Add inverter time sensor (special handling for BCD time format)
    sensors.append(
        SajR5MqttInverterTimeSensorEntity(
            coordinator=saj_data.coordinator_realtime_data,
            description=SajR5MqttSensorEntityDescription(
                key="inverter_time",
                entity_registry_enabled_default=True,
                device_class=SensorDeviceClass.TIMESTAMP,
                state_class=None,
                native_unit_of_measurement=None,
                modbus_register_offset=0x6E,  # 0x0137
                modbus_register_data_type="8s",  # 4 words = 8 bytes
                modbus_register_scale=None,
                value_fn=None,
            ),
        )
    )

    # Create inverter data sensors
    if saj_data.coordinator_inverter_data:
        for description in SAJ_INVERTER_DATA_SENSOR_DESCRIPTIONS:
            sensors.append(
                SajR5MqttSensorEntity(
                    coordinator=saj_data.coordinator_inverter_data,
                    description=description,
                )
            )

    # Create config data sensors
    if saj_data.coordinator_config_data:
        for description in SAJ_CONFIG_DATA_SENSOR_DESCRIPTIONS:
            sensors.append(
                SajR5MqttSensorEntity(
                    coordinator=saj_data.coordinator_config_data,
                    description=description,
                )
            )

    async_add_entities(sensors)


class SajR5MqttSensorEntity(SajR5MqttEntity, SensorEntity):
    """SAJ R5 MQTT sensor entity."""

    entity_description: SajR5MqttSensorEntityDescription

    def __init__(
        self,
        coordinator: SajR5MqttDataCoordinator,
        description: SajR5MqttSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description)

    @property
    def _entity_type(self) -> str:
        """Return the entity type."""
        return "sensor"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None

        return get_entity_description(
            self.coordinator.data, self.entity_description
        )


class SajR5MqttInverterTimeSensorEntity(SajR5MqttSensorEntity):
    """SAJ R5 MQTT inverter time sensor entity with BCD parsing."""

    @property
    def native_value(self) -> datetime | None:
        """Return the inverter time as datetime."""
        if self.coordinator.data is None:
            return None

        try:
            # Read 4 words (8 bytes) starting from offset
            offset = self.entity_description.modbus_register_offset
            time_data = self.coordinator.data[offset : offset + 8]

            if len(time_data) < 8:
                return None

            # Parse BCD time: yyyyMMddHHmmsszz (4 words)
            # Each byte is BCD (0x20 = 20, 0x25 = 25, etc.)
            year = (time_data[0] << 8) | time_data[1]
            month = time_data[2]
            day = time_data[3]
            hour = time_data[4]
            minute = time_data[5]
            second = time_data[6]

            # Create datetime object
            dt = datetime(year, month, day, hour, minute, second)

            # Use local timezone
            return dt.replace(tzinfo=ZoneInfo("UTC"))

        except (ValueError, IndexError) as ex:
            LOGGER.warning(f"Failed to parse inverter time: {ex}")
            return None
