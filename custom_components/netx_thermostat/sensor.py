"""Sensor platform for NetX Thermostat integration."""
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .climate import NetXDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NetX Thermostat sensor platform."""
    # Get the coordinator from the climate setup
    coordinator = None
    for entry_id, data in hass.data.get(DOMAIN, {}).items():
        if entry_id == config_entry.entry_id:
            # The coordinator is shared, we need to get it
            # For now, we'll create sensors that will be populated once climate is set up
            pass
    
    # We'll access the coordinator through the climate entity
    # For this implementation, we create a simpler approach
    from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
    
    host = config_entry.data[CONF_HOST]
    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    
    coordinator = NetXDataUpdateCoordinator(hass, host, username, password)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        NetXCO2Sensor(coordinator, config_entry, "co2_level", "CO2 Level"),
        NetXCO2Sensor(coordinator, config_entry, "co2_peak_level", "CO2 Peak Level"),
        NetXCO2Sensor(coordinator, config_entry, "co2_alert_level", "CO2 Alert Level"),
    ]

    async_add_entities(sensors)


class NetXCO2Sensor(CoordinatorEntity, SensorEntity):
    """Representation of a NetX CO2 Sensor."""

    _attr_device_class = SensorDeviceClass.CO2
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        name: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "NetX Thermostat",
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._sensor_type)
        if value is not None:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def available(self):
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data.get(self._sensor_type) is not None
        )
