"""Climate platform for NetX Thermostat integration."""
import logging
import asyncio

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
    ENDPOINT_INDEX_HTM,
)
from .coordinator import NetXDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NetX Thermostat climate platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]

    async_add_entities([NetXClimate(coordinator, config_entry)])


class NetXClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a NetX Thermostat."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
    )
    _attr_hvac_modes = [
        HVACMode.OFF, 
        HVACMode.HEAT, 
        HVACMode.COOL, 
        HVACMode.HEAT_COOL,  # AUTO mode
        HVACMode.FAN_ONLY,
    ]
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP

    def __init__(
        self, 
        coordinator: NetXDataUpdateCoordinator, 
        config_entry: ConfigEntry
    ) -> None:
        """Initialize the thermostat."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_climate"
        
        # Use custom device name if provided, otherwise use default
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
            "suggested_area": "Living Room",
        }
        self._attr_icon = "mdi:thermostat"

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation."""
        sysstat = self.coordinator.data.get("sysstat", "IDLE")
        fan = self.coordinator.data.get("curfan", "AUTO")
        
        # Check system status for active heating/cooling
        if "HEAT" in sysstat.upper():
            return HVACAction.HEATING
        elif "COOL" in sysstat.upper():
            return HVACAction.COOLING
        elif fan == "ON" and sysstat == "IDLE":
            return HVACAction.FAN
        elif sysstat == "IDLE":
            return HVACAction.IDLE
        else:
            return HVACAction.IDLE

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        temp = self.coordinator.data.get("curtemp")
        return float(temp) if temp and temp != "--" else None

    @property
    def current_humidity(self) -> int | None:
        """Return the current humidity."""
        humidity = self.coordinator.data.get("humidity")
        if humidity and humidity != "--":
            try:
                return int(humidity)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        mode = self.hvac_mode
        if mode == HVACMode.HEAT:
            temp = self.coordinator.data.get("sptheat")
        elif mode == HVACMode.COOL:
            temp = self.coordinator.data.get("sptcool")
        elif mode == HVACMode.HEAT_COOL:
            # In AUTO mode, return None to indicate range should be used
            return None
        else:
            return None
        return float(temp) if temp and temp != "--" else None

    @property
    def target_temperature_high(self) -> float | None:
        """Return the highbound target temperature."""
        temp = self.coordinator.data.get("sptcool")
        return float(temp) if temp and temp != "--" else None

    @property
    def target_temperature_low(self) -> float | None:
        """Return the lowbound target temperature."""
        temp = self.coordinator.data.get("sptheat")
        return float(temp) if temp and temp != "--" else None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation mode."""
        mode = self.coordinator.data.get("curmode", "OFF")
        fan = self.coordinator.data.get("curfan", "AUTO")
        
        # If mode is OFF but fan is ON, we're in fan-only mode
        if mode == "OFF" and fan == "ON":
            return HVACMode.FAN_ONLY
        elif mode == "HEAT":
            return HVACMode.HEAT
        elif mode == "COOL":
            return HVACMode.COOL
        elif mode == "AUTO":
            return HVACMode.HEAT_COOL
        else:
            return HVACMode.OFF

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = {}
        
        # Add system status
        sysstat = self.coordinator.data.get("sysstat")
        if sysstat:
            attrs["system_status"] = sysstat
        
        # Add schedule status
        schedstat = self.coordinator.data.get("schedstat")
        if schedstat:
            attrs["schedule_status"] = schedstat
            
        # Add manual/schedule mode
        manual_program = self.coordinator.data.get("manual_program")
        if manual_program is not None:
            attrs["manual_mode"] = manual_program == "1"
        
        # Add CO2 data if available
        if self.coordinator.data.get("co2_level"):
            attrs["co2_level"] = self.coordinator.data.get("co2_level")
        if self.coordinator.data.get("co2_peak_level"):
            attrs["co2_peak_level"] = self.coordinator.data.get("co2_peak_level")
        if self.coordinator.data.get("co2_alert_level"):
            attrs["co2_alert_level"] = self.coordinator.data.get("co2_alert_level")
        
        # Add fan status
        fan = self.coordinator.data.get("curfan")
        if fan:
            attrs["fan_mode"] = fan
            
        # Add override status
        isoverride = self.coordinator.data.get("isoverride")
        if isoverride is not None:
            attrs["override_active"] = isoverride == "1"
            
        return attrs

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            temp = kwargs[ATTR_TEMPERATURE]
            
            # Clamp temperature to valid range
            temp = max(MIN_TEMP, min(MAX_TEMP, temp))
            
            mode = self.hvac_mode
            if mode == HVACMode.HEAT:
                await self._set_heat_setpoint(temp)
            elif mode == HVACMode.COOL:
                await self._set_cool_setpoint(temp)
            elif mode == HVACMode.HEAT_COOL:
                # In AUTO mode, set both if only one temp provided
                # This maintains the current deadband
                pass
        
        # Handle range setting (for AUTO mode)
        if "target_temp_low" in kwargs:
            temp_low = max(MIN_TEMP, min(MAX_TEMP, kwargs["target_temp_low"]))
            await self._set_heat_setpoint(temp_low)
        
        if "target_temp_high" in kwargs:
            temp_high = max(MIN_TEMP, min(MAX_TEMP, kwargs["target_temp_high"]))
            await self._set_cool_setpoint(temp_high)
        
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.HEAT:
            await self._set_mode("HEAT")
            await self._set_fan("AUTO")
        elif hvac_mode == HVACMode.COOL:
            await self._set_mode("COOL")
            await self._set_fan("AUTO")
        elif hvac_mode == HVACMode.HEAT_COOL:
            await self._set_mode("AUTO")
            await self._set_fan("AUTO")
        elif hvac_mode == HVACMode.FAN_ONLY:
            await self._set_fan_only()
        elif hvac_mode == HVACMode.OFF:
            await self._set_mode("OFF")
            await self._set_fan("AUTO")
        
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()

    async def _set_heat_setpoint(self, temperature: float) -> None:
        """Set heating setpoint."""
        data = {"sp_heat": int(temperature), "update": "Update"}
        await self.coordinator.async_send_command(ENDPOINT_INDEX_HTM, data)

    async def _set_cool_setpoint(self, temperature: float) -> None:
        """Set cooling setpoint."""
        data = {"sp_cool": int(temperature), "update": "Update"}
        await self.coordinator.async_send_command(ENDPOINT_INDEX_HTM, data)

    async def _set_mode(self, mode: str) -> None:
        """Set thermostat mode."""
        data = {"mode": mode, "update": "Update"}
        await self.coordinator.async_send_command(ENDPOINT_INDEX_HTM, data)

    async def _set_fan_only(self) -> None:
        """Set fan-only mode."""
        # First turn off heating/cooling mode
        await self._set_mode("OFF")
        await asyncio.sleep(0.5)  # Small delay between commands
        
        # Then turn on the fan
        data = {"fan": "ON", "update": "Update"}
        await self.coordinator.async_send_command(ENDPOINT_INDEX_HTM, data)

    async def _set_fan(self, fan_mode: str) -> None:
        """Set fan mode (ON or AUTO)."""
        data = {"fan": fan_mode, "update": "Update"}
        await self.coordinator.async_send_command(ENDPOINT_INDEX_HTM, data)
