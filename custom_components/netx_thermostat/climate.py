"""Climate platform for NetX Thermostat integration."""
import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MIN_TEMP,
    MAX_TEMP,
)
from .coordinator import NetXTCPDataUpdateCoordinator
from .api import NetXThermostatAPI

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NetX Thermostat climate platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities([NetXTCPClimate(coordinator, api, config_entry)])


class NetXTCPClimate(CoordinatorEntity[NetXTCPDataUpdateCoordinator], ClimateEntity):
    """Representation of a NetX Thermostat."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.FAN_MODE
    )
    _attr_hvac_modes = [
        HVACMode.OFF, 
        HVACMode.HEAT, 
        HVACMode.COOL, 
        HVACMode.HEAT_COOL,  # AUTO
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = ["auto", "on"]
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP

    def __init__(
        self, 
        coordinator: NetXTCPDataUpdateCoordinator,
        api: NetXThermostatAPI,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_climate"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        if self.coordinator.data and self.coordinator.data.temp_scale == "C":
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if self.coordinator.data:
            return self.coordinator.data.indoor_temp
        return None

    @property
    def current_humidity(self) -> int | None:
        """Return the current humidity."""
        if self.coordinator.data and self.coordinator.data.humidity:
            # Only return humidity if it's a valid reading (not 0 which often means no sensor)
            humidity = self.coordinator.data.humidity
            return humidity if humidity > 0 else None
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach (for single setpoint modes)."""
        if not self.coordinator.data:
            return None
        
        mode = self.hvac_mode
        if mode == HVACMode.HEAT:
            return self.coordinator.data.heat_setpoint
        elif mode == HVACMode.COOL:
            return self.coordinator.data.cool_setpoint
        # For AUTO/HEAT_COOL, return None to use range instead
        return None

    @property
    def target_temperature_high(self) -> float | None:
        """Return the upper bound target temperature (cooling setpoint)."""
        if self.coordinator.data:
            return self.coordinator.data.cool_setpoint
        return None

    @property
    def target_temperature_low(self) -> float | None:
        """Return the lower bound target temperature (heating setpoint)."""
        if self.coordinator.data:
            return self.coordinator.data.heat_setpoint
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if not self.coordinator.data:
            return HVACMode.OFF
        
        mode = self.coordinator.data.hvac_mode
        fan = self.coordinator.data.fan_mode
        
        if mode == "OFF":
            # Check if it's fan-only mode
            if fan == "ON":
                return HVACMode.FAN_ONLY
            return HVACMode.OFF
        elif mode == "HEAT":
            return HVACMode.HEAT
        elif mode == "COOL":
            return HVACMode.COOL
        elif mode == "AUTO":
            return HVACMode.HEAT_COOL
        
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation."""
        if not self.coordinator.data:
            return None
        
        status = self.coordinator.data.operating_status
        fan = self.coordinator.data.fan_mode
        
        if status == "HEAT":
            return HVACAction.HEATING
        elif status == "COOL":
            return HVACAction.COOLING
        elif status in ("OFF", "IDLE", None):
            # Check if fan is running
            if fan == "ON":
                return HVACAction.FAN
            return HVACAction.IDLE
        
        return HVACAction.IDLE

    @property
    def fan_mode(self) -> str | None:
        """Return the current fan mode."""
        if self.coordinator.data:
            return self.coordinator.data.fan_mode.lower() if self.coordinator.data.fan_mode else "auto"
        return "auto"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.data:
            state = self.coordinator.data
            attrs["operation_mode"] = state.operation_mode
            attrs["is_manual_mode"] = state.is_manual_mode
            attrs["override_active"] = state.override_active
            attrs["recovery_active"] = state.recovery_active
            attrs["operating_status"] = state.operating_status
            
            if state.stage:
                attrs["stage"] = state.stage
            if state.event:
                attrs["event"] = state.event
            if state.outdoor_temp is not None:
                attrs["outdoor_temperature"] = state.outdoor_temp
            if state.last_error:
                attrs["last_error"] = state.last_error
        
        return attrs

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self._api.async_set_hvac_mode("OFF")
            await self._api.async_set_fan_mode("AUTO")
        elif hvac_mode == HVACMode.HEAT:
            await self._api.async_set_hvac_mode("HEAT")
        elif hvac_mode == HVACMode.COOL:
            await self._api.async_set_hvac_mode("COOL")
        elif hvac_mode == HVACMode.HEAT_COOL:
            await self._api.async_set_hvac_mode("AUTO")
        elif hvac_mode == HVACMode.FAN_ONLY:
            await self._api.async_set_hvac_mode("OFF")
            await self._api.async_set_fan_mode("ON")
        
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self._api.async_set_fan_mode(fan_mode.upper())
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            # Single temperature - set based on current mode
            temp = int(kwargs[ATTR_TEMPERATURE])
            mode = self.hvac_mode
            
            if mode == HVACMode.HEAT:
                await self._api.async_set_heat_setpoint(temp)
            elif mode == HVACMode.COOL:
                await self._api.async_set_cool_setpoint(temp)
            else:
                # For AUTO or other modes, set both (maintaining deadband)
                await self._api.async_set_heat_setpoint(temp)
                await self._api.async_set_cool_setpoint(temp + 3)  # Default 3° deadband
        
        # Handle temperature range (for AUTO mode)
        if "target_temp_low" in kwargs:
            await self._api.async_set_heat_setpoint(int(kwargs["target_temp_low"]))
        
        if "target_temp_high" in kwargs:
            await self._api.async_set_cool_setpoint(int(kwargs["target_temp_high"]))
        
        await self.coordinator.async_request_refresh()
