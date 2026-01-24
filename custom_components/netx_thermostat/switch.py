"""Switch platform for NetX Thermostat integration."""
import logging

from homeassistant.components.switch import SwitchEntity
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
    """Set up the NetX Thermostat switch platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    switches = [
        NetXFanSwitch(coordinator, api, config_entry),
        NetXHumIndependentSwitch(coordinator, api, config_entry),
        NetXDehumIndependentSwitch(coordinator, api, config_entry),
    ]

    async_add_entities(switches)


class NetXFanSwitch(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SwitchEntity):
    """Representation of a NetX Thermostat Fan Switch."""

    _attr_has_entity_name = True
    _attr_name = "Fan"
    _attr_icon = "mdi:fan"

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        api: NetXThermostatAPI,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_fan_switch"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def is_on(self) -> bool:
        """Return true if fan is on."""
        if self.coordinator.data:
            return self.coordinator.data.fan_mode == "ON"
        return False

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the fan on."""
        await self._api.async_set_fan_mode("ON")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the fan off (set to AUTO)."""
        await self._api.async_set_fan_mode("AUTO")
        await self.coordinator.async_request_refresh()


class NetXHumIndependentSwitch(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SwitchEntity):
    """Humidification Independent Mode Switch."""

    _attr_has_entity_name = True
    _attr_name = "Humidify Independent Mode"
    _attr_icon = "mdi:water-plus-outline"

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        api: NetXThermostatAPI,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_hum_independent"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def is_on(self) -> bool:
        """Return true if humidification runs independently of heating."""
        if self.coordinator.data and self.coordinator.data.hum_control_mode:
            return self.coordinator.data.hum_control_mode == "IH"
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.hum_control_mode is not None
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "description": (
                "When ON (IH), humidification runs independently of heating. "
                "When OFF (WH), humidification only runs when heating is active."
            ),
            "mode_code": self.coordinator.data.hum_control_mode if self.coordinator.data else None,
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Set humidification to run independently (IH)."""
        state = self.coordinator.data
        setpoint = state.hum_setpoint if state and state.hum_setpoint else 50
        variance = state.hum_variance if state and state.hum_variance else 5
        
        await self._api.async_set_humidification(True, setpoint, variance)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Set humidification to run with heating (WH)."""
        state = self.coordinator.data
        setpoint = state.hum_setpoint if state and state.hum_setpoint else 50
        variance = state.hum_variance if state and state.hum_variance else 5
        
        await self._api.async_set_humidification(False, setpoint, variance)
        await self.coordinator.async_request_refresh()


class NetXDehumIndependentSwitch(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SwitchEntity):
    """Dehumidification Independent Mode Switch."""

    _attr_has_entity_name = True
    _attr_name = "Dehumidify Independent Mode"
    _attr_icon = "mdi:water-minus-outline"

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        api: NetXThermostatAPI,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_dehum_independent"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def is_on(self) -> bool:
        """Return true if dehumidification runs independently of cooling."""
        if self.coordinator.data and self.coordinator.data.dehum_control_mode:
            return self.coordinator.data.dehum_control_mode == "IC"
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.dehum_control_mode is not None
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "description": (
                "When ON (IC), dehumidification runs independently of cooling. "
                "When OFF (WC), dehumidification only runs when cooling is active."
            ),
            "mode_code": self.coordinator.data.dehum_control_mode if self.coordinator.data else None,
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Set dehumidification to run independently (IC)."""
        state = self.coordinator.data
        setpoint = state.dehum_setpoint if state and state.dehum_setpoint else 55
        variance = state.dehum_variance if state and state.dehum_variance else 5
        
        await self._api.async_set_dehumidification(True, setpoint, variance)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Set dehumidification to run with cooling (WC)."""
        state = self.coordinator.data
        setpoint = state.dehum_setpoint if state and state.dehum_setpoint else 55
        variance = state.dehum_variance if state and state.dehum_variance else 5
        
        await self._api.async_set_dehumidification(False, setpoint, variance)
        await self.coordinator.async_request_refresh()
