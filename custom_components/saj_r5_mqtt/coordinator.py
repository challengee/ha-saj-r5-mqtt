"""Coordinators for the SAJ R5 MQTT integration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import SajR5MqttClient
from .const import DOMAIN, LOGGER
from .utils import log_hex


@dataclass
class SajR5MqttData:
    """SAJ R5 MQTT data."""

    mqtt_client: SajR5MqttClient
    coordinator_realtime_data: SajR5MqttRealtimeDataCoordinator
    coordinator_inverter_data: SajR5MqttInverterDataCoordinator | None

    def mark_coordinators_ready(self) -> None:
        """Mark all coordinators ready."""
        self.coordinator_realtime_data.ready = True
        if self.coordinator_inverter_data:
            self.coordinator_inverter_data.ready = True

    async def async_refresh_coordinators(self) -> None:
        """Refresh all coordinators."""
        await self.coordinator_realtime_data.async_refresh()
        if self.coordinator_inverter_data:
            await self.coordinator_inverter_data.async_refresh()

    async def async_first_refresh(self) -> None:
        """Trigger first refresh for all coordinators."""
        LOGGER.debug("Triggering coordinator(s) first refresh")
        self.mark_coordinators_ready()
        await self.async_refresh_coordinators()


class SajR5MqttDataCoordinator(DataUpdateCoordinator, ABC):
    """SAJ R5 MQTT data coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        mqtt_client: SajR5MqttClient,
        scan_interval: timedelta,
        name: str,
    ) -> None:
        """Set up the SajR5MqttDataCoordinator class."""
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{name}_coordinator",
            update_interval=scan_interval,
        )
        self.mqtt_client = mqtt_client
        self.data: bytearray | None = None
        self.ready = False

    @abstractmethod
    async def _async_fetch_data(self) -> bytearray | None:
        """Fetch the latest data from the source."""
        raise NotImplementedError

    async def _async_update_data(self) -> bytearray | None:
        # If coordinator is not ready (due to mqtt discovery), skip the fetching of the data
        if not self.ready:
            LOGGER.debug(f"Skipping data fetching, {self.name} not ready yet")
            return None
        return await self._async_fetch_data()


class SajR5MqttRealtimeDataCoordinator(SajR5MqttDataCoordinator):
    """SAJ R5 MQTT realtime data coordinator."""

    async def _async_fetch_data(self) -> bytearray | None:
        """Fetch the realtime data."""
        reg_start = 0x0100
        reg_count = 0x38  # 56 registers (0x0100-0x0137)
        LOGGER.debug(
            f"Fetching realtime data at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)


class SajR5MqttInverterDataCoordinator(SajR5MqttDataCoordinator):
    """SAJ R5 MQTT inverter data coordinator."""

    async def _async_fetch_data(self) -> bytearray | None:
        """Fetch the inverter data."""
        reg_start = 0x8F00
        reg_count = 0x1D  # 29 registers (0x8F00-0x8F1C, removed BatNum)
        LOGGER.debug(
            f"Fetching inverter data at {log_hex(reg_start)}, length: {log_hex(reg_count)}"
        )
        return await self.mqtt_client.read_registers(reg_start, reg_count)
