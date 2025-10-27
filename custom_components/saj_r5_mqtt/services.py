"""Services for the SAJ R5 MQTT integration."""

from __future__ import annotations

from struct import unpack_from

import voluptuous as vol

from homeassistant import core
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import ConfigEntrySelector

from .const import (
    ATTR_CONFIG_ENTRY,
    ATTR_REGISTER,
    ATTR_REGISTER_FORMAT,
    ATTR_REGISTER_SIZE,
    ATTR_REGISTER_VALUE,
    DOMAIN,
    LOGGER,
    SERVICE_READ_REGISTER,
    SERVICE_REFRESH_INVERTER_DATA,
    SERVICE_WRITE_REGISTER,
)
from .types import SajR5MqttConfigEntry


def async_register_services(hass: HomeAssistant) -> None:
    """Register services for SAJ R5 MQTT integration."""

    async def read_register(call: ServiceCall) -> core.ServiceResponse:
        LOGGER.debug("Reading register")
        entry = _get_config_entry(hass, call.data.get(ATTR_CONFIG_ENTRY, None))
        mqtt_client = entry.runtime_data.mqtt_client
        attr_register: str = call.data[ATTR_REGISTER]
        attr_register_size: str = call.data[ATTR_REGISTER_SIZE]
        attr_register_format: str | None = call.data[ATTR_REGISTER_FORMAT]
        # Validate input
        try:
            if attr_register.startswith("0x"):
                register_start = int(attr_register, 16)
            else:
                register_start = int(attr_register)
        except ValueError as e:
            LOGGER.error(f"Invalid register: {attr_register}")
            raise ServiceValidationError("Invalid register", DOMAIN) from e
        try:
            if attr_register_size.startswith("0x"):
                register_size = int(attr_register_size, 16)
            else:
                register_size = int(attr_register_size)
        except ValueError as e:
            LOGGER.error(f"Invalid register size: {attr_register_size}")
            raise ServiceValidationError("Invalid register value") from e
        if attr_register_format and not attr_register_format.startswith(">"):
            msg = f"Invalid register format: {attr_register_format}"
            LOGGER.error(msg)
            raise ServiceValidationError("Invalid register format")
        # Read register
        content = await mqtt_client.read_registers(register_start, register_size)
        # Return response (format if needed, otherwise return bytes)
        if attr_register_format:
            (result,) = unpack_from(attr_register_format, content, 0)
            return {"value": str(result)}
        return {"value": ":".join(f"{b:02x}" for b in content)}

    if not hass.services.has_service(DOMAIN, SERVICE_READ_REGISTER):
        LOGGER.debug(f"Registering service: {SERVICE_READ_REGISTER}")
        hass.services.async_register(
            DOMAIN,
            SERVICE_READ_REGISTER,
            read_register,
            schema=vol.Schema(
                vol.All(
                    {
                        vol.Optional(ATTR_CONFIG_ENTRY): ConfigEntrySelector(),
                        vol.Required(ATTR_REGISTER): cv.string,
                        vol.Required(ATTR_REGISTER_SIZE): cv.string,
                        vol.Optional(ATTR_REGISTER_FORMAT, default=None): vol.Any(
                            cv.string, None
                        ),
                    }
                )
            ),
            supports_response=SupportsResponse.ONLY,
        )

    async def write_register(call: ServiceCall) -> None:
        LOGGER.debug("Writing register")
        entry = _get_config_entry(hass, call.data.get(ATTR_CONFIG_ENTRY, None))
        mqtt_client = entry.runtime_data.mqtt_client
        attr_register: str = call.data[ATTR_REGISTER]
        attr_register_value: str = call.data[ATTR_REGISTER_VALUE]
        # Validate input
        try:
            if attr_register.startswith("0x"):
                register = int(attr_register, 16)
            else:
                register = int(attr_register)
        except ValueError as e:
            LOGGER.error(f"Invalid register: {attr_register}")
            raise ServiceValidationError("Invalid register") from e
        try:
            if attr_register_value.startswith("0x"):
                value = int(attr_register_value, 16)
            else:
                value = int(attr_register_value)
        except ValueError as e:
            LOGGER.error(f"Invalid register value: {attr_register_value}")
            raise ServiceValidationError("Invalid register value") from e
        # Write register
        await mqtt_client.write_register(register, value)

    if not hass.services.has_service(DOMAIN, SERVICE_WRITE_REGISTER):
        LOGGER.debug(f"Registering service: {SERVICE_WRITE_REGISTER}")
        hass.services.async_register(
            DOMAIN,
            SERVICE_WRITE_REGISTER,
            write_register,
            schema=vol.Schema(
                vol.All(
                    {
                        vol.Optional(ATTR_CONFIG_ENTRY): ConfigEntrySelector(),
                        vol.Required(ATTR_REGISTER): cv.string,
                        vol.Required(ATTR_REGISTER_VALUE): cv.string,
                    }
                )
            ),
        )

    async def refresh_inverter_data(call: ServiceCall) -> None:
        # Only refresh when coordinator is enabled
        entry = _get_config_entry(hass, call.data.get(ATTR_CONFIG_ENTRY, None))
        coordinator = entry.runtime_data.coordinator_inverter_data
        if coordinator:
            LOGGER.debug("Refreshing inverter data")
            await coordinator.async_request_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_INVERTER_DATA):
        LOGGER.debug(f"Registering service: {SERVICE_REFRESH_INVERTER_DATA}")
        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_INVERTER_DATA,
            refresh_inverter_data,
            schema=vol.Schema(
                vol.All({vol.Optional(ATTR_CONFIG_ENTRY): ConfigEntrySelector()})
            ),
        )


def async_remove_services(hass: HomeAssistant) -> None:
    """Remove all services."""
    hass.services.async_remove(DOMAIN, SERVICE_READ_REGISTER)
    hass.services.async_remove(DOMAIN, SERVICE_WRITE_REGISTER)
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_INVERTER_DATA)


def _get_config_entry(
    hass: HomeAssistant, entry_id: str | None = None
) -> SajR5MqttConfigEntry:
    """Return the config entry or raise error if not found or not loaded."""
    # Get the specified config entry, or fallback to first one if not specified
    if not (entry := hass.config_entries.async_get_entry(entry_id)):
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries or len(entries) == 0:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_found",
            )
        else:
            entry = entries[0]
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_not_loaded",
        )
    return entry
