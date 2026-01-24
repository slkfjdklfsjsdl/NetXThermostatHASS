"""Climate platform for NetX Thermostat integration."""
import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MIN_TEMP,
    MAX_TEMP,
    PRESET_NONE,
    PRESET_HUMIDIFY,
    PRESET_DEHUMIDIFY,
    PRESET_TO_RELAY,
    RELAY_TO_PRESET,
)
from .coordinator import NetXDataUpdateCoordinator
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

    async_add_entities([NetXClimate(coordinator, api, config_entry)])


class NetXClimate(CoordinatorEntity[NetXDataUpdateCoordinator], ClimateEntity):
    """Representation of a NetX Thermostat."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = ["auto", "on"]
    _attr_preset_modes = [PRESET_NONE, PRESET_HUMIDIFY, PRESET_DEHUMIDIFY]
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
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
        """Return the current humidity (from HTTP API)."""
        if self.coordinator.data and self.coordinator.data.humidity:
            return self.coordinator.data.humidity
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if not self.coordinator.data:
            return None
        
        mode = self.hvac_mode
        if mode == HVACMode.HEAT:
            return self.coordinator.data.heat_setpoint
        elif mode == HVACMode.COOL:
            return self.coordinator.data.cool_setpoint
        return None

    @property
    def target_temperature_high(self) -> float | None:
        """Return the upper bound target temperature."""
        if self.coordinator.data:
            return self.coordinator.data.cool_setpoint
        return None

    @property
    def target_temperature_low(self) -> float | None:
        """Return the lower bound target temperature."""
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
        
        state = self.coordinator.data
        
        # Use stage to determine if idle
        if state.is_idle:
            # Stage is 0, so we're idle
            if state.fan_mode == "ON":
                return HVACAction.FAN
            return HVACAction.IDLE
        
        # Stage >= 1, actively running
        if state.operating_status == "HEAT":
            return HVACAction.HEATING
        elif state.operating_status == "COOL":
            return HVACAction.COOLING
        
        return HVACAction.IDLE

    @property
    def fan_mode(self) -> str | None:
        """Return the current fan mode."""
        if self.coordinator.data:
            return self.coordinator.data.fan_mode.lower() if self.coordinator.data.fan_mode else "auto"
        return "auto"

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode (humidity relay mode)."""
        if self.coordinator.data and self.coordinator.data.relay1_mode:
            mode = self.coordinator.data.relay1_mode.upper()
            return RELAY_TO_PRESET.get(mode, PRESET_NONE)
        return PRESET_NONE

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
            attrs["stage"] = state.stage
            attrs["is_idle"] = state.is_idle
            
            if state.event:
                attrs["event"] = state.event
            if state.outdoor_temp is not None:
                attrs["outdoor_temperature"] = state.outdoor_temp
            if state.relay_state:
                attrs["relay_state"] = state.relay_state
            if state.co2_level is not None:
                attrs["co2_level"] = state.co2_level
            
            # Humidity settings
            if state.hum_setpoint is not None:
                attrs["humidify_setpoint"] = state.hum_setpoint
                attrs["humidify_variance"] = state.hum_variance
                attrs["humidify_mode"] = "Independent" if state.hum_control_mode == "IH" else "With Heating"
            if state.dehum_setpoint is not None:
                attrs["dehumidify_setpoint"] = state.dehum_setpoint
                attrs["dehumidify_variance"] = state.dehum_variance
                attrs["dehumidify_mode"] = "Independent" if state.dehum_control_mode == "IC" else "With Cooling"
        
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

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode (humidity relay mode)."""
        relay_mode = PRESET_TO_RELAY.get(preset_mode, "OFF")
        await self._api.async_set_relay_mode(relay_mode)
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            temp = int(kwargs[ATTR_TEMPERATURE])
            mode = self.hvac_mode
            
            if mode == HVACMode.HEAT:
                await self._api.async_set_heat_setpoint(temp)
            elif mode == HVACMode.COOL:
                await self._api.async_set_cool_setpoint(temp)
            else:
                await self._api.async_set_heat_setpoint(temp)
                await self._api.async_set_cool_setpoint(temp + 3)
        
        if "target_temp_low" in kwargs:
            await self._api.async_set_heat_setpoint(int(kwargs["target_temp_low"]))
        
        if "target_temp_high" in kwargs:
            await self._api.async_set_cool_setpoint(int(kwargs["target_temp_high"]))
        
        await self.coordinator.async_request_refresh()
