"""Base entity for the SAJ R5 MQTT integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from struct import unpack_from

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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
from .coordinator import SajR5MqttDataCoordinator


@dataclass(frozen=True, kw_only=True)
class SajR5MqttEntityDescription(EntityDescription):
    """A class that describes SAJ R5 MQTT entities."""

    # Modbus register details for reading from coordinator
    modbus_register_offset: int
    modbus_register_data_type: str
    modbus_register_scale: float | str | None
    # Custom value function
    value_fn: Callable[[int | float | str | None], int | float | str | None] | None


class SajR5MqttEntity(CoordinatorEntity[SajR5MqttDataCoordinator], Entity, ABC):
    """SAJ R5 MQTT entity.

    This is the base abstract class for all entity classes.
    """

    def __init__(
        self,
        coordinator: SajR5MqttDataCoordinator,
        description: SajR5MqttEntityDescription | None = None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        # Do not remove this assignment, used internally in hass
        self.entity_description: SajR5MqttEntityDescription = description

        # Copy values from entity description
        self._offset = description.modbus_register_offset
        self._data_type = description.modbus_register_data_type
        self._scale = description.modbus_register_scale
        self._value_fn = description.value_fn

        # Define entity prefixes
        self._serial_number = coordinator.config_entry.data[CONF_SERIAL_NUMBER]
        self._use_serial_number_prefix = coordinator.config_entry.options[
            CONF_ENABLE_SERIAL_NUMBER_PREFIX
        ]
        self._unique_id_prefix = f"{BRAND}_{self._serial_number}"
        self._name_prefix = (
            f"{BRAND}_{self._serial_number}"
            if self._use_serial_number_prefix
            else f"{BRAND}_{MODEL_SHORT}"
        )

        # Set entity attributes (use _entity_type in _attr_unique_id to support sensors with same key, but different type)
        self._attr_unique_id = (
            f"{self._unique_id_prefix}_{description.key}_{self._entity_type}".lower()
        )
        self._attr_name = f"{self._name_prefix}_{description.key}".lower()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
            name=f"{BRAND} {self._serial_number}",
            manufacturer=MANUFACTURER,
            model=MODEL,
            serial_number=self._serial_number,
        )

        LOGGER.debug(f"Setting up entity: {self.name}")

    def _custom_native_value(
        self, value: float | str | None
    ) -> int | float | str | None:
        """Return the custom native value to represent the entity state.

        Returns by default the native value from the coordinator.
        To be replaced by classes who want to have custom logic.
        """
        return value

    def _get_native_value(self) -> int | float | str | None:
        """Get the native value for the entity."""
        # Return None if no coordinator data
        payload = self.coordinator.data
        if payload is None:
            return None

        value: int | float | str | None = None
        try:
            # Get raw sensor value (>Sxx is custom type to indicate a string of length xx)
            if self._data_type.startswith(">S"):
                reg_length = int(self._data_type.replace(">S", ""))
                value = bytearray.decode(
                    payload[self._offset : self._offset + reg_length]
                )
            else:
                (value,) = unpack_from(
                    self._data_type,
                    payload,
                    self._offset,
                )

            # Set sensor value (taking scale into account, scale should ALWAYS contain a .)
            if self._scale is not None:
                digits = max(0, str(self._scale)[::-1].find("."))
                value = round(value * float(self._scale), digits)
                # If scale is a str, format the value with the same precision
                if isinstance(self._scale, str):
                    value = "{:.{precision}f}".format(value, precision=digits)

            # Value conversion function
            if self._value_fn:
                value = self._value_fn(value)

            # Custom native value implementation
            value = self._custom_native_value(value)

        except Exception as e:
            LOGGER.error(
                f"Unable to get native value for entity: {self.entity_id or self.name}",
                e,
            )
            return None

        if self.entity_id:
            LOGGER.debug(
                f"Entity: {self.entity_id}, value: {value}{' ' + self.unit_of_measurement if self.unit_of_measurement else ''}"
            )
        else:
            # Used for internal entities (no entity_id)
            LOGGER.debug(f"-> Internal entity: {self.name}, value: {value}")

        return value

    @property
    @abstractmethod
    def _entity_type(self) -> str:
        pass


def get_entity_description_by_key(
    descriptions: tuple[EntityDescription], key: str
) -> EntityDescription | None:
    """Get an entity description by its 'key' from a tuple of entity descriptions."""
    description = next(
        (d for d in descriptions if d.key == key),
        None,
    )
    if description is None:
        raise ValueError(f"Invalid entity description key: {key}")
    return description


def get_entity_description(
    payload: bytearray, description: SajR5MqttEntityDescription
) -> int | float | str | None:
    """Extract and parse a value from payload based on entity description."""
    if payload is None:
        return None

    value: int | float | str | None = None
    try:
        # Get raw sensor value
        if description.modbus_register_data_type.endswith("s"):
            # String type (e.g., "20s")
            reg_length = int(description.modbus_register_data_type.replace("s", ""))
            value = payload[description.modbus_register_offset : description.modbus_register_offset + reg_length]
            if isinstance(value, (bytes, bytearray)):
                value = value.decode("ascii", errors="ignore").rstrip("\x00")
        else:
            # Numeric type
            (value,) = unpack_from(
                description.modbus_register_data_type,
                payload,
                description.modbus_register_offset,
            )

        # Apply scale if present
        if description.modbus_register_scale is not None:
            digits = max(0, str(description.modbus_register_scale)[::-1].find("."))
            value = round(value * float(description.modbus_register_scale), digits)
            if isinstance(description.modbus_register_scale, str):
                value = "{:.{precision}f}".format(value, precision=digits)

        # Apply value conversion function if present
        if description.value_fn:
            value = description.value_fn(value)

    except Exception as e:
        LOGGER.error(f"Unable to get value for {description.key}: {e}")
        return None

    return value
