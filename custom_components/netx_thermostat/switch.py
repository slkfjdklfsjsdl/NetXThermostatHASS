"""Switch platform for NetX Thermostat integration."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NetXDataUpdateCoordinator
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
        NetXHumIndependentSwitch(coordinator, api, config_entry),
        NetXDehumIndependentSwitch(coordinator, api, config_entry),
    ]

    async_add_entities(switches)


class NetXBaseSwitch(CoordinatorEntity[NetXDataUpdateCoordinator], SwitchEntity):
    """Base class for NetX switches."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        api: NetXThermostatAPI,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }
        self._config_entry = config_entry


class NetXHumIndependentSwitch(NetXBaseSwitch):
    """Humidification Independent Mode Switch."""

    _attr_name = "Humidify Independent Mode"
    _attr_icon = "mdi:water-plus-outline"

    def __init__(self, coordinator, api, config_entry) -> None:
        """Initialize."""
        super().__init__(coordinator, api, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_hum_independent"

    @property
    def is_on(self) -> bool:
        """Return true if independent mode is enabled."""
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
        """Set to independent mode (IH)."""
        state = self.coordinator.data
        setpoint = state.hum_setpoint if state and state.hum_setpoint else 50
        variance = state.hum_variance if state and state.hum_variance else 5
        
        await self._api.async_set_humidification(True, setpoint, variance)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Set to with heating mode (WH)."""
        state = self.coordinator.data
        setpoint = state.hum_setpoint if state and state.hum_setpoint else 50
        variance = state.hum_variance if state and state.hum_variance else 5
        
        await self._api.async_set_humidification(False, setpoint, variance)
        await self.coordinator.async_request_refresh()


class NetXDehumIndependentSwitch(NetXBaseSwitch):
    """Dehumidification Independent Mode Switch."""

    _attr_name = "Dehumidify Independent Mode"
    _attr_icon = "mdi:water-minus-outline"

    def __init__(self, coordinator, api, config_entry) -> None:
        """Initialize."""
        super().__init__(coordinator, api, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_dehum_independent"

    @property
    def is_on(self) -> bool:
        """Return true if independent mode is enabled."""
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
        """Set to independent mode (IC)."""
        state = self.coordinator.data
        setpoint = state.dehum_setpoint if state and state.dehum_setpoint else 55
        variance = state.dehum_variance if state and state.dehum_variance else 5
        
        await self._api.async_set_dehumidification(True, setpoint, variance)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Set to with cooling mode (WC)."""
        state = self.coordinator.data
        setpoint = state.dehum_setpoint if state and state.dehum_setpoint else 55
        variance = state.dehum_variance if state and state.dehum_variance else 5
        
        await self._api.async_set_dehumidification(False, setpoint, variance)
        await self.coordinator.async_request_refresh()
