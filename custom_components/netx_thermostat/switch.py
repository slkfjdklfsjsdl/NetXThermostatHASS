"""Switch platform for NetX Thermostat integration."""
import logging
import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ENDPOINT_INDEX_HTM,
    ENDPOINT_CONFIG_HUMIDITY,
)
from .coordinator import NetXDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NetX Thermostat switch platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]

    switches = [
        NetXFanSwitch(coordinator, config_entry),
        NetXDehumIndependentSwitch(coordinator, config_entry),
        NetXHumIndependentSwitch(coordinator, config_entry),
        NetXAuxRelaySwitch(coordinator, config_entry),
    ]

    async_add_entities(switches)


class NetXFanSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a NetX Thermostat Fan Switch."""

    _attr_has_entity_name = True
    _attr_name = "Fan"
    _attr_icon = "mdi:fan"

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_fan_switch"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def is_on(self) -> bool:
        """Return true if fan is on."""
        fan_mode = self.coordinator.data.get("curfan", "AUTO")
        return fan_mode == "ON"

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the fan on."""
        data = {"fan": "ON", "update": "Update"}
        success = await self.coordinator.async_send_command(ENDPOINT_INDEX_HTM, data)
        
        if success:
            _LOGGER.info("Fan turned on successfully")
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn on fan")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the fan off (set to AUTO)."""
        data = {"fan": "AUTO", "update": "Update"}
        success = await self.coordinator.async_send_command(ENDPOINT_INDEX_HTM, data)
        
        if success:
            _LOGGER.info("Fan turned off (AUTO) successfully")
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn off fan")


class NetXDehumIndependentSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Dehumidification Independent Mode Switch."""

    _attr_has_entity_name = True
    _attr_name = "Dehumidify Independent Mode"
    _attr_icon = "mdi:water-minus-outline"

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_dehum_independent"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def is_on(self) -> bool:
        """Return true if dehumidification runs independently of cooling."""
        independent = self.coordinator.data.get("dehum_independent", 0)
        return independent == 1

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data.get("dehum_independent") is not None
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "description": (
                "When ON, dehumidification runs independently of cooling. "
                "When OFF, dehumidification only runs when cooling is active."
            )
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Set dehumidification to run independently."""
        setpoint = self.coordinator.data.get("dehum_setpoint", 55)
        variance = self.coordinator.data.get("dehum_variance", 5)
        
        data = {
            "dehum": 1,  # Independent of Cooling
            "spdehum": setpoint,
            "spvdehum": variance,
            "ap_dhum": "Apply",
        }
        
        success = await self.coordinator.async_send_command(
            ENDPOINT_CONFIG_HUMIDITY, data
        )
        
        if success:
            _LOGGER.info("Dehumidification set to independent mode")
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set dehumidification to independent mode")

    async def async_turn_off(self, **kwargs) -> None:
        """Set dehumidification to run with cooling only."""
        setpoint = self.coordinator.data.get("dehum_setpoint", 55)
        variance = self.coordinator.data.get("dehum_variance", 5)
        
        data = {
            "dehum": 0,  # With Cooling Only
            "spdehum": setpoint,
            "spvdehum": variance,
            "ap_dhum": "Apply",
        }
        
        success = await self.coordinator.async_send_command(
            ENDPOINT_CONFIG_HUMIDITY, data
        )
        
        if success:
            _LOGGER.info("Dehumidification set to run with cooling only")
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set dehumidification to run with cooling")


class NetXHumIndependentSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Humidification Independent Mode Switch."""

    _attr_has_entity_name = True
    _attr_name = "Humidify Independent Mode"
    _attr_icon = "mdi:water-plus-outline"

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_hum_independent"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def is_on(self) -> bool:
        """Return true if humidification runs independently of heating."""
        independent = self.coordinator.data.get("hum_independent", 0)
        return independent == 1

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data.get("hum_independent") is not None
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "description": (
                "When ON, humidification runs independently of heating. "
                "When OFF, humidification only runs when heating is active."
            )
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Set humidification to run independently."""
        setpoint = self.coordinator.data.get("hum_setpoint", 35)
        variance = self.coordinator.data.get("hum_variance", 5)
        
        data = {
            "hum": 1,  # Independent of Heating
            "sphum": setpoint,
            "spvhum": variance,
            "ap_hum": "Apply",
        }
        
        success = await self.coordinator.async_send_command(
            ENDPOINT_CONFIG_HUMIDITY, data
        )
        
        if success:
            _LOGGER.info("Humidification set to independent mode")
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set humidification to independent mode")

    async def async_turn_off(self, **kwargs) -> None:
        """Set humidification to run with heating only."""
        setpoint = self.coordinator.data.get("hum_setpoint", 35)
        variance = self.coordinator.data.get("hum_variance", 5)
        
        data = {
            "hum": 0,  # With Heating Only
            "sphum": setpoint,
            "spvhum": variance,
            "ap_hum": "Apply",
        }
        
        success = await self.coordinator.async_send_command(
            ENDPOINT_CONFIG_HUMIDITY, data
        )
        
        if success:
            _LOGGER.info("Humidification set to run with heating only")
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set humidification to run with heating")


class NetXAuxRelaySwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Aux Relay Switch."""

    _attr_has_entity_name = True
    _attr_name = "Aux Relay"
    _attr_icon = "mdi:electric-switch"

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_aux_relay"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def is_on(self) -> bool:
        """Return true if aux relay is on."""
        aux = self.coordinator.data.get("aux_relay", 0)
        return aux == 1

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data.get("aux_relay") is not None
        )

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the aux relay on."""
        data = {"aux1": 1, "ap_aux": "Apply"}
        success = await self.coordinator.async_send_command(
            ENDPOINT_CONFIG_HUMIDITY, data
        )
        
        if success:
            _LOGGER.info("Aux relay turned on")
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn on aux relay")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the aux relay off."""
        data = {"aux1": 0, "ap_aux": "Apply"}
        success = await self.coordinator.async_send_command(
            ENDPOINT_CONFIG_HUMIDITY, data
        )
        
        if success:
            _LOGGER.info("Aux relay turned off")
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn off aux relay")
