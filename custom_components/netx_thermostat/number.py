"""Number platform for NetX Thermostat integration."""
import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NetXTCPDataUpdateCoordinator
from .api import NetXThermostatAPI

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NetX Thermostat number platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    entities = [
        NetXHumSetpointNumber(coordinator, api, config_entry),
        NetXHumVarianceNumber(coordinator, api, config_entry),
        NetXDehumSetpointNumber(coordinator, api, config_entry),
        NetXDehumVarianceNumber(coordinator, api, config_entry),
    ]

    async_add_entities(entities)


class NetXHumSetpointNumber(CoordinatorEntity[NetXTCPDataUpdateCoordinator], NumberEntity):
    """Humidification setpoint control."""

    _attr_has_entity_name = True
    _attr_name = "Humidify Below"
    _attr_icon = "mdi:water-plus"
    _attr_native_min_value = 10
    _attr_native_max_value = 90
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        api: NetXThermostatAPI,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_hum_setpoint"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data and self.coordinator.data.hum_setpoint is not None:
            return float(self.coordinator.data.hum_setpoint)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.hum_setpoint is not None
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the humidification setpoint."""
        state = self.coordinator.data
        independent = state.hum_control_mode == "IH" if state else False
        variance = state.hum_variance if state and state.hum_variance else 5
        
        await self._api.async_set_humidification(independent, int(value), variance)
        await self.coordinator.async_request_refresh()


class NetXHumVarianceNumber(CoordinatorEntity[NetXTCPDataUpdateCoordinator], NumberEntity):
    """Humidification variance control."""

    _attr_has_entity_name = True
    _attr_name = "Humidify Variance"
    _attr_icon = "mdi:plus-minus-variant"
    _attr_native_min_value = 2
    _attr_native_max_value = 10
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        api: NetXThermostatAPI,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_hum_variance"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data and self.coordinator.data.hum_variance is not None:
            return float(self.coordinator.data.hum_variance)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.hum_variance is not None
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the humidification variance."""
        state = self.coordinator.data
        independent = state.hum_control_mode == "IH" if state else False
        setpoint = state.hum_setpoint if state and state.hum_setpoint else 50
        
        await self._api.async_set_humidification(independent, setpoint, int(value))
        await self.coordinator.async_request_refresh()


class NetXDehumSetpointNumber(CoordinatorEntity[NetXTCPDataUpdateCoordinator], NumberEntity):
    """Dehumidification setpoint control."""

    _attr_has_entity_name = True
    _attr_name = "Dehumidify Above"
    _attr_icon = "mdi:water-minus"
    _attr_native_min_value = 10
    _attr_native_max_value = 90
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        api: NetXThermostatAPI,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_dehum_setpoint"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data and self.coordinator.data.dehum_setpoint is not None:
            return float(self.coordinator.data.dehum_setpoint)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.dehum_setpoint is not None
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the dehumidification setpoint."""
        state = self.coordinator.data
        independent = state.dehum_control_mode == "IC" if state else True
        variance = state.dehum_variance if state and state.dehum_variance else 5
        
        await self._api.async_set_dehumidification(independent, int(value), variance)
        await self.coordinator.async_request_refresh()


class NetXDehumVarianceNumber(CoordinatorEntity[NetXTCPDataUpdateCoordinator], NumberEntity):
    """Dehumidification variance control."""

    _attr_has_entity_name = True
    _attr_name = "Dehumidify Variance"
    _attr_icon = "mdi:plus-minus-variant"
    _attr_native_min_value = 2
    _attr_native_max_value = 10
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        api: NetXThermostatAPI,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_dehum_variance"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data and self.coordinator.data.dehum_variance is not None:
            return float(self.coordinator.data.dehum_variance)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.dehum_variance is not None
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set the dehumidification variance."""
        state = self.coordinator.data
        independent = state.dehum_control_mode == "IC" if state else True
        setpoint = state.dehum_setpoint if state and state.dehum_setpoint else 55
        
        await self._api.async_set_dehumidification(independent, setpoint, int(value))
        await self.coordinator.async_request_refresh()
