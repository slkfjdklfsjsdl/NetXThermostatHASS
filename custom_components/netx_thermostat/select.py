"""Select platform for NetX Thermostat integration."""
import logging
import asyncio

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    RELAY_MODES,
    RELAY_MODES_REVERSE,
    ENDPOINT_CONFIG_HUMIDITY,
)
from .coordinator import NetXDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NetX Thermostat select platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]

    entities = [
        NetXHumidityRelayModeSelect(coordinator, config_entry),
    ]

    async_add_entities(entities)


class NetXHumidityRelayModeSelect(CoordinatorEntity, SelectEntity):
    """Representation of the Humidity Relay Mode selector."""

    _attr_has_entity_name = True
    _attr_name = "Humidity Relay Mode"
    _attr_icon = "mdi:water-percent"
    _attr_options = list(RELAY_MODES.values())

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_humidity_relay_mode"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        relay_mode = self.coordinator.data.get("humidity_relay_mode")
        if relay_mode is not None:
            return RELAY_MODES.get(relay_mode, "Off")
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data.get("humidity_relay_mode") is not None
        )

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        relay_value = RELAY_MODES_REVERSE.get(option)
        if relay_value is None:
            _LOGGER.error("Invalid relay mode option: %s", option)
            return

        data = {"rel1": relay_value, "ap_rel": "Apply"}
        success = await self.coordinator.async_send_command(
            ENDPOINT_CONFIG_HUMIDITY, data
        )
        
        if success:
            await asyncio.sleep(1)
            await self.coordinator.async_request_refresh()
