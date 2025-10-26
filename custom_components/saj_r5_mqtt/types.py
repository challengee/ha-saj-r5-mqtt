"""Types for the SAJ R5 MQTT integration."""

from homeassistant.config_entries import ConfigEntry

from .coordinator import SajR5MqttData

type SajR5MqttConfigEntry = ConfigEntry[SajR5MqttData]
