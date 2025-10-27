"""Number platform for SAJ R5 MQTT integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BRAND,
    CONF_ENABLE_SERIAL_NUMBER_PREFIX,
    CONF_SERIAL_NUMBER,
    DOMAIN,
    LOGGER,
    MANUFACTURER,
    MODEL,
    MODEL_SHORT,
)
from .types import SajR5MqttConfigEntry


@dataclass(frozen=True, kw_only=True)
class SajR5MqttNumberEntityDescription(NumberEntityDescription):
    """Describes SAJ R5 MQTT number entity."""

    modbus_register: int
    """The modbus register address to write to."""

    value_scale: float = 1.0
    """Scale factor to apply before writing (multiply)."""


NUMBER_TYPES: tuple[SajR5MqttNumberEntityDescription, ...] = (
    SajR5MqttNumberEntityDescription(
        key="power_limit",
        translation_key="power_limit",
        native_min_value=0,
        native_max_value=110,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:solar-power",
        modbus_register=0x801F,
        value_scale=10.0,  # Value multiplied by 10 before writing (from modbus R5 implementation)
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SajR5MqttConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SAJ R5 MQTT number entities."""
    saj_data = entry.runtime_data

    entities = [
        SajR5MqttNumber(
            saj_data=saj_data,
            serial_number=entry.data[CONF_SERIAL_NUMBER],
            use_serial_number_prefix=entry.options[CONF_ENABLE_SERIAL_NUMBER_PREFIX],
            description=description,
        )
        for description in NUMBER_TYPES
    ]

    async_add_entities(entities)


class SajR5MqttNumber(NumberEntity, Entity):
    """Representation of a SAJ R5 MQTT number entity."""

    entity_description: SajR5MqttNumberEntityDescription

    def __init__(
        self,
        saj_data,
        serial_number: str,
        use_serial_number_prefix: bool,
        description: SajR5MqttNumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        self._saj_data = saj_data
        self._serial_number = serial_number
        self.entity_description = description

        # Define name prefix based on user configuration
        name_prefix = (
            f"{BRAND}_{serial_number}"
            if use_serial_number_prefix
            else f"{BRAND}_{MODEL_SHORT}"
        )

        # Set unique ID and name
        self._attr_unique_id = f"{BRAND}_{serial_number}_{description.key}_number".lower()
        self._attr_name = f"{name_prefix}_{description.key}".lower()

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial_number)},
            name=f"{BRAND} {serial_number}",
            manufacturer=MANUFACTURER,
            model=MODEL,
            serial_number=serial_number,
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value (not readable from inverter)."""
        # These registers are write-only, so we can't read the current value
        # Return None to indicate value is unknown
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value by writing to the inverter."""
        # Scale the value according to the description
        scaled_value = int(value * self.entity_description.value_scale)

        LOGGER.debug(
            f"Setting {self.entity_description.key} to {value} "
            f"(scaled: {scaled_value}) at register {hex(self.entity_description.modbus_register)}"
        )

        # Write the register using the MQTT client
        result = await self._saj_data.mqtt_client.write_register(
            register=self.entity_description.modbus_register,
            value=scaled_value,
        )

        if result is None:
            msg = f"Failed to write {self.entity_description.key}={value} to register {hex(self.entity_description.modbus_register)}"
            LOGGER.error(msg)
            raise HomeAssistantError(msg)

        LOGGER.info(
            f"Successfully set {self.entity_description.key} to {value}"
        )
