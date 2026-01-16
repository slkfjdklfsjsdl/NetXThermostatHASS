"""Number platform for NetX Thermostat integration."""
import logging
import asyncio

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ENDPOINT_CONFIG_HUMIDITY,
)
from .coordinator import NetXDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NetX Thermostat number platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]

    entities = [
        # Dehumidification controls
        NetXDehumSetpointNumber(coordinator, config_entry),
        NetXDehumVarianceNumber(coordinator, config_entry),
        # Humidification controls
        NetXHumSetpointNumber(coordinator, config_entry),
        NetXHumVarianceNumber(coordinator, config_entry),
    ]

    async_add_entities(entities)


class NetXDehumSetpointNumber(CoordinatorEntity, NumberEntity):
    """Representation of the Dehumidification Setpoint control."""

    _attr_has_entity_name = True
    _attr_name = "Dehumidify Above"
    _attr_icon = "mdi:water-minus"
    _attr_native_min_value = 35
    _attr_native_max_value = 75
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_dehum_setpoint"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        setpoint = self.coordinator.data.get("dehum_setpoint")
        if setpoint is not None:
            return float(setpoint)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data.get("dehum_setpoint") is not None
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the dehumidification setpoint."""
        # Get current values to preserve them
        variance = self.coordinator.data.get("dehum_variance", 5)
        independent = self.coordinator.data.get("dehum_independent", 0)
        
        data = {
            "dehum": independent,
            "spdehum": int(value),
            "spvdehum": variance,
            "ap_dhum": "Apply",
        }
        
        success = await self.coordinator.async_send_command(
            ENDPOINT_CONFIG_HUMIDITY, data
        )
        
        if success:
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()


class NetXDehumVarianceNumber(CoordinatorEntity, NumberEntity):
    """Representation of the Dehumidification Variance control."""

    _attr_has_entity_name = True
    _attr_name = "Dehumidify Variance"
    _attr_icon = "mdi:plus-minus-variant"
    _attr_native_min_value = 2
    _attr_native_max_value = 5
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_dehum_variance"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        variance = self.coordinator.data.get("dehum_variance")
        if variance is not None:
            return float(variance)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data.get("dehum_variance") is not None
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the dehumidification variance."""
        # Get current values to preserve them
        setpoint = self.coordinator.data.get("dehum_setpoint", 55)
        independent = self.coordinator.data.get("dehum_independent", 0)
        
        data = {
            "dehum": independent,
            "spdehum": setpoint,
            "spvdehum": int(value),
            "ap_dhum": "Apply",
        }
        
        success = await self.coordinator.async_send_command(
            ENDPOINT_CONFIG_HUMIDITY, data
        )
        
        if success:
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()


class NetXHumSetpointNumber(CoordinatorEntity, NumberEntity):
    """Representation of the Humidification Setpoint control."""

    _attr_has_entity_name = True
    _attr_name = "Humidify Below"
    _attr_icon = "mdi:water-plus"
    _attr_native_min_value = 10
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_hum_setpoint"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        setpoint = self.coordinator.data.get("hum_setpoint")
        if setpoint is not None:
            return float(setpoint)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data.get("hum_setpoint") is not None
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the humidification setpoint."""
        # Get current values to preserve them
        variance = self.coordinator.data.get("hum_variance", 5)
        independent = self.coordinator.data.get("hum_independent", 0)
        
        data = {
            "hum": independent,
            "sphum": int(value),
            "spvhum": variance,
            "ap_hum": "Apply",
        }
        
        success = await self.coordinator.async_send_command(
            ENDPOINT_CONFIG_HUMIDITY, data
        )
        
        if success:
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()


class NetXHumVarianceNumber(CoordinatorEntity, NumberEntity):
    """Representation of the Humidification Variance control."""

    _attr_has_entity_name = True
    _attr_name = "Humidify Variance"
    _attr_icon = "mdi:plus-minus-variant"
    _attr_native_min_value = 2
    _attr_native_max_value = 5
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_hum_variance"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        variance = self.coordinator.data.get("hum_variance")
        if variance is not None:
            return float(variance)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data.get("hum_variance") is not None
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the humidification variance."""
        # Get current values to preserve them
        setpoint = self.coordinator.data.get("hum_setpoint", 35)
        independent = self.coordinator.data.get("hum_independent", 0)
        
        data = {
            "hum": independent,
            "sphum": setpoint,
            "spvhum": int(value),
            "ap_hum": "Apply",
        }
        
        success = await self.coordinator.async_send_command(
            ENDPOINT_CONFIG_HUMIDITY, data
        )
        
        if success:
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
