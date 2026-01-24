"""Sensor platform for NetX Thermostat integration."""
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NetXTCPDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NetX Thermostat sensor platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]

    sensors = [
        NetXOutdoorTemperatureSensor(coordinator, config_entry),
        NetXHumiditySensor(coordinator, config_entry),
        NetXOperationModeSensor(coordinator, config_entry),
        NetXOperatingStatusSensor(coordinator, config_entry),
        NetXStageSensor(coordinator, config_entry),
        NetXRelayStateSensor(coordinator, config_entry),
        NetXHumControlModeSensor(coordinator, config_entry),
        NetXDehumControlModeSensor(coordinator, config_entry),
    ]

    async_add_entities(sensors)


class NetXOutdoorTemperatureSensor(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SensorEntity):
    """Outdoor temperature sensor."""

    _attr_has_entity_name = True
    _attr_name = "Outdoor Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:thermometer"

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_outdoor_temp"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        if self.coordinator.data and self.coordinator.data.temp_scale == "C":
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def native_value(self) -> float | None:
        """Return the outdoor temperature."""
        if self.coordinator.data:
            return self.coordinator.data.outdoor_temp
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.outdoor_temp is not None
        )


class NetXHumiditySensor(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SensorEntity):
    """Humidity sensor."""

    _attr_has_entity_name = True
    _attr_name = "Humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:water-percent"

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_humidity"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_value(self) -> int | None:
        """Return the humidity."""
        if self.coordinator.data and self.coordinator.data.humidity:
            humidity = self.coordinator.data.humidity
            # Return None if humidity is 0 (often means no sensor)
            return humidity if humidity > 0 else None
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.humidity is not None
            and self.coordinator.data.humidity > 0
        )


class NetXOperationModeSensor(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SensorEntity):
    """Operation mode sensor (Manual vs Schedule)."""

    _attr_has_entity_name = True
    _attr_name = "Operation Mode"
    _attr_icon = "mdi:cog"

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_operation_mode"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_value(self) -> str | None:
        """Return the operation mode."""
        if self.coordinator.data:
            return self.coordinator.data.operation_mode
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.data:
            attrs["is_manual_mode"] = self.coordinator.data.is_manual_mode
        return attrs


class NetXOperatingStatusSensor(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SensorEntity):
    """Operating status sensor (what's actually running)."""

    _attr_has_entity_name = True
    _attr_name = "Operating Status"
    _attr_icon = "mdi:hvac"

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_operating_status"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_value(self) -> str | None:
        """Return the operating status."""
        if self.coordinator.data:
            status = self.coordinator.data.operating_status
            return status.capitalize() if status else "Idle"
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.data:
            attrs["override_active"] = self.coordinator.data.override_active
            attrs["recovery_active"] = self.coordinator.data.recovery_active
            if self.coordinator.data.event:
                attrs["event"] = self.coordinator.data.event
        return attrs


class NetXStageSensor(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SensorEntity):
    """Stage sensor (heating/cooling stage)."""

    _attr_has_entity_name = True
    _attr_name = "Stage"
    _attr_icon = "mdi:stairs"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_stage"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_value(self) -> int | None:
        """Return the current stage."""
        if self.coordinator.data:
            return self.coordinator.data.stage
        return None


class NetXRelayStateSensor(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SensorEntity):
    """Relay state sensor."""

    _attr_has_entity_name = True
    _attr_name = "Relay State"
    _attr_icon = "mdi:electric-switch"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_relay_state"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_value(self) -> str | None:
        """Return the relay state."""
        if self.coordinator.data and self.coordinator.data.relay_state:
            return self.coordinator.data.relay_state
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.relay_state is not None
        )


class NetXHumControlModeSensor(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SensorEntity):
    """Humidification control mode sensor."""

    _attr_has_entity_name = True
    _attr_name = "Humidification Mode"
    _attr_icon = "mdi:water-plus"

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_hum_mode"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_value(self) -> str | None:
        """Return the humidification mode."""
        if self.coordinator.data and self.coordinator.data.hum_control_mode:
            mode = self.coordinator.data.hum_control_mode
            if mode == "IH":
                return "Independent of Heating"
            elif mode == "WH":
                return "With Heating"
            return mode
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.data:
            attrs["mode_code"] = self.coordinator.data.hum_control_mode
            if self.coordinator.data.hum_setpoint is not None:
                attrs["setpoint"] = self.coordinator.data.hum_setpoint
            if self.coordinator.data.hum_variance is not None:
                attrs["variance"] = self.coordinator.data.hum_variance
        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.hum_control_mode is not None
        )


class NetXDehumControlModeSensor(CoordinatorEntity[NetXTCPDataUpdateCoordinator], SensorEntity):
    """Dehumidification control mode sensor."""

    _attr_has_entity_name = True
    _attr_name = "Dehumidification Mode"
    _attr_icon = "mdi:water-minus"

    def __init__(
        self,
        coordinator: NetXTCPDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_dehum_mode"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }

    @property
    def native_value(self) -> str | None:
        """Return the dehumidification mode."""
        if self.coordinator.data and self.coordinator.data.dehum_control_mode:
            mode = self.coordinator.data.dehum_control_mode
            if mode == "IC":
                return "Independent of Cooling"
            elif mode == "WC":
                return "With Cooling"
            return mode
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.data:
            attrs["mode_code"] = self.coordinator.data.dehum_control_mode
            if self.coordinator.data.dehum_setpoint is not None:
                attrs["setpoint"] = self.coordinator.data.dehum_setpoint
            if self.coordinator.data.dehum_variance is not None:
                attrs["variance"] = self.coordinator.data.dehum_variance
        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.dehum_control_mode is not None
        )
