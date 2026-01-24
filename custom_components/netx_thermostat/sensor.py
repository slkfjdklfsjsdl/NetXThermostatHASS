"""Sensor platform for NetX Thermostat integration."""
import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfTemperature, PERCENTAGE, CONCENTRATION_PARTS_PER_MILLION
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NetXDataUpdateCoordinator

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
        NetXCO2Sensor(coordinator, config_entry),
        NetXCO2PeakSensor(coordinator, config_entry),
        NetXOperationModeSensor(coordinator, config_entry),
        NetXOperatingStatusSensor(coordinator, config_entry),
        NetXStageSensor(coordinator, config_entry),
        NetXHumControlModeSensor(coordinator, config_entry),
        NetXDehumControlModeSensor(coordinator, config_entry),
    ]

    async_add_entities(sensors)


class NetXBaseSensor(CoordinatorEntity[NetXDataUpdateCoordinator], SensorEntity):
    """Base class for NetX sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NetXDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Network Thermostat",
        }
        self._config_entry = config_entry


class NetXOutdoorTemperatureSensor(NetXBaseSensor):
    """Outdoor temperature sensor."""

    _attr_name = "Outdoor Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:thermometer"

    def __init__(self, coordinator: NetXDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_outdoor_temp"

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


class NetXHumiditySensor(NetXBaseSensor):
    """Humidity sensor (from HTTP API)."""

    _attr_name = "Humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:water-percent"

    def __init__(self, coordinator: NetXDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_humidity"

    @property
    def native_value(self) -> int | None:
        """Return the humidity."""
        if self.coordinator.data:
            return self.coordinator.data.humidity
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

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {"source": "HTTP API (/index.xml)"}


class NetXCO2Sensor(NetXBaseSensor):
    """CO2 sensor (from HTTP API)."""

    _attr_name = "CO2"
    _attr_device_class = SensorDeviceClass.CO2
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION
    _attr_icon = "mdi:molecule-co2"

    def __init__(self, coordinator: NetXDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_co2"

    @property
    def native_value(self) -> int | None:
        """Return the CO2 level."""
        if self.coordinator.data:
            return self.coordinator.data.co2_level
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.co2_level is not None
            and self.coordinator.data.co2_level > 0
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = {"source": "HTTP API (/co2.json)"}
        if self.coordinator.data:
            if self.coordinator.data.co2_alert_level:
                attrs["alert_level"] = self.coordinator.data.co2_alert_level
            attrs["in_alert"] = self.coordinator.data.co2_in_alert
        return attrs


class NetXCO2PeakSensor(NetXBaseSensor):
    """CO2 Peak sensor (from HTTP API)."""

    _attr_name = "CO2 Peak"
    _attr_device_class = SensorDeviceClass.CO2
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION
    _attr_icon = "mdi:molecule-co2"

    def __init__(self, coordinator: NetXDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_co2_peak"

    @property
    def native_value(self) -> int | None:
        """Return the peak CO2 level."""
        if self.coordinator.data:
            return self.coordinator.data.co2_peak_level
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.co2_peak_level is not None
            and self.coordinator.data.co2_peak_level > 0
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {"source": "HTTP API (/co2.json)", "description": "Peak CO2 level since last reset"}


class NetXOperationModeSensor(NetXBaseSensor):
    """Operation mode sensor (Manual vs Schedule)."""

    _attr_name = "Operation Mode"
    _attr_icon = "mdi:cog"

    def __init__(self, coordinator: NetXDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_operation_mode"

    @property
    def native_value(self) -> str | None:
        """Return the operation mode."""
        if self.coordinator.data:
            return self.coordinator.data.operation_mode
        return None


class NetXOperatingStatusSensor(NetXBaseSensor):
    """Operating status sensor."""

    _attr_name = "Operating Status"
    _attr_icon = "mdi:hvac"

    def __init__(self, coordinator: NetXDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_operating_status"

    @property
    def native_value(self) -> str | None:
        """Return the operating status."""
        if self.coordinator.data:
            state = self.coordinator.data
            if state.is_idle:
                return "Idle"
            return state.operating_status.capitalize() if state.operating_status else "Idle"
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.data:
            attrs["stage"] = self.coordinator.data.stage
            attrs["is_idle"] = self.coordinator.data.is_idle
            attrs["override_active"] = self.coordinator.data.override_active
            attrs["recovery_active"] = self.coordinator.data.recovery_active
            if self.coordinator.data.event:
                attrs["event"] = self.coordinator.data.event
        return attrs


class NetXStageSensor(NetXBaseSensor):
    """Stage sensor."""

    _attr_name = "Stage"
    _attr_icon = "mdi:stairs"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NetXDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_stage"

    @property
    def native_value(self) -> int | None:
        """Return the current stage."""
        if self.coordinator.data:
            return self.coordinator.data.stage
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = {}
        if self.coordinator.data:
            stage = self.coordinator.data.stage
            if stage == 0:
                attrs["description"] = "Idle - at setpoint"
            elif stage == 1:
                attrs["description"] = "Stage 1 active"
            elif stage == 2:
                attrs["description"] = "Stage 2 active"
            elif stage and stage >= 3:
                attrs["description"] = f"Stage {stage} active"
        return attrs


class NetXHumControlModeSensor(NetXBaseSensor):
    """Humidification control mode sensor."""

    _attr_name = "Humidification Mode"
    _attr_icon = "mdi:water-plus"

    def __init__(self, coordinator: NetXDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_hum_mode"

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


class NetXDehumControlModeSensor(NetXBaseSensor):
    """Dehumidification control mode sensor."""

    _attr_name = "Dehumidification Mode"
    _attr_icon = "mdi:water-minus"

    def __init__(self, coordinator: NetXDataUpdateCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_dehum_mode"

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
