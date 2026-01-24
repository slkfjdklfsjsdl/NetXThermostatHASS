"""Select platform for NetX Thermostat integration."""
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NetXTCPDataUpdateCoordinator
from .api import NetXThermostatAPI

_LOGGER = logging.getLogger(__name__)

RELAY_MODE_OPTIONS = ["Off", "Humidify", "Dehumidify"]
RELAY_MODE_MAP = {
    "Off": "OFF",
    "Humidify": "HUM",
    "Dehumidify": "DEHUM",
}
RELAY_MODE_REVERSE = {
    "OFF": "Off",
    "HUM": "Humidify",
    "DEHUM": "Dehumidify",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NetX Thermostat select platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    entities = [
        NetXRelayModeSelect(coordinator, api, config_entry),
    ]

    async_add_entities(entities)


class NetXRelayModeSelect(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SelectEntity):
    """Humidity relay mode selector."""

    _attr_has_entity_name = True
    _attr_name = "Humidity Relay Mode"
    _attr_icon = "mdi:water-percent"
    _attr_options = RELAY_MODE_OPTIONS

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        api: NetXThermostatAPI,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._api = api
        self._attr_unique_id = f"{config_entry.entry_id}_relay_mode"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if self.coordinator.data and self.coordinator.data.relay1_mode:
            mode = self.coordinator.data.relay1_mode.upper()
            return RELAY_MODE_REVERSE.get(mode, "Off")
        return "Off"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.relay1_mode is not None
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.data:
            if self.coordinator.data.relay_state:
                attrs["relay_state"] = self.coordinator.data.relay_state
            if self.coordinator.data.relay2_mode:
                attrs["relay2_mode"] = self.coordinator.data.relay2_mode
        return attrs

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        api_mode = RELAY_MODE_MAP.get(option, "OFF")
        await self._api.async_set_relay_mode(api_mode)
        await self.coordinator.async_request_refresh()
