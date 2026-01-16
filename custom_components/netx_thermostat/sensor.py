"""Sensor platform for NetX Thermostat integration."""
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfTemperature,
)
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
        # CO2 Level Sensors (Category: None - these are primary sensors)
        NetXCO2Sensor(coordinator, config_entry, "co2_level", "CO2 Level", "mdi:molecule-co2", None),
        NetXCO2Sensor(coordinator, config_entry, "co2_peak_level", "CO2 Peak Level", "mdi:chart-line", None),
        NetXCO2Sensor(coordinator, config_entry, "co2_alert_level", "CO2 Alert Level", "mdi:alert-circle", None),
        
        # CO2 Binary/Text Sensors (Category: Diagnostic)
        NetXTextSensor(coordinator, config_entry, "co2_type", "CO2 Type", "mdi:information", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "co2_valid", "CO2 Valid", "mdi:check-circle", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "co2_in_alert", "CO2 In Alert", "mdi:alert", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "co2_peak_reset", "CO2 Peak Reset", "mdi:restore", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "co2_display", "CO2 Display", "mdi:monitor", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "co2_relay_high", "CO2 Relay High", "mdi:electric-switch", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "co2_relay_failure", "CO2 Relay Failure", "mdi:alert-circle", EntityCategory.DIAGNOSTIC),
        
        # Auxiliary Temperature Sensors
        NetXTemperatureSensor(coordinator, config_entry, "outdoor", "Outdoor Temperature", "mdi:thermometer", None),
        
        # Humidity Sensors
        NetXHumiditySensor(coordinator, config_entry, "outhum", "Outdoor Humidity", "mdi:water-percent", None),
        
        # Schedule/Program Sensors - Important status sensors
        NetXTextSensor(coordinator, config_entry, "schedstat", "Schedule Status", "mdi:calendar-clock", None),
        NetXTextSensor(coordinator, config_entry, "cursched", "Current Schedule", "mdi:calendar-check", None),
        NetXTextSensor(coordinator, config_entry, "sysstat", "System Status", "mdi:hvac", None),
        
        # Manual/Schedule Mode sensor
        NetXManualModeSensor(coordinator, config_entry),
        
        # Today's Schedule sensor
        NetXScheduleSensor(coordinator, config_entry),
        
        # Schedule/Program Sensors - Diagnostic
        NetXTextSensor(coordinator, config_entry, "schedstat1", "Schedule Status 1", "mdi:calendar-check", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "isoverride", "Override Active", "mdi:lock-open", EntityCategory.DIAGNOSTIC),
        
        # Setpoint Sensors (Occupied/Unoccupied) - Diagnostic
        NetXTemperatureSensor(coordinator, config_entry, "ul_occ_cool", "Upper Occupied Cool", "mdi:thermometer-high", EntityCategory.DIAGNOSTIC),
        NetXTemperatureSensor(coordinator, config_entry, "l_occ_cool", "Lower Occupied Cool", "mdi:thermometer-low", EntityCategory.DIAGNOSTIC),
        NetXTemperatureSensor(coordinator, config_entry, "ul_unocc_cool", "Upper Unoccupied Cool", "mdi:thermometer-high", EntityCategory.DIAGNOSTIC),
        NetXTemperatureSensor(coordinator, config_entry, "l_unocc_cool", "Lower Unoccupied Cool", "mdi:thermometer-low", EntityCategory.DIAGNOSTIC),
        NetXTemperatureSensor(coordinator, config_entry, "ul_occ_heat", "Upper Occupied Heat", "mdi:thermometer-high", EntityCategory.DIAGNOSTIC),
        NetXTemperatureSensor(coordinator, config_entry, "l_occ_heat", "Lower Occupied Heat", "mdi:thermometer-low", EntityCategory.DIAGNOSTIC),
        NetXTemperatureSensor(coordinator, config_entry, "ul_unocc_heat", "Upper Unoccupied Heat", "mdi:thermometer-high", EntityCategory.DIAGNOSTIC),
        NetXTemperatureSensor(coordinator, config_entry, "l_unocc_heat", "Lower Unoccupied Heat", "mdi:thermometer-low", EntityCategory.DIAGNOSTIC),
        
        # Indicator Sensors - Diagnostic
        NetXTextSensor(coordinator, config_entry, "ind0", "Indicator 0", "mdi:numeric-0-circle", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "ind1", "Indicator 1", "mdi:numeric-1-circle", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "ind2", "Indicator 2", "mdi:numeric-2-circle", EntityCategory.DIAGNOSTIC),
        
        # System Status Sensors - Diagnostic
        NetXTextSensor(coordinator, config_entry, "sysadapt", "System Adapt", "mdi:auto-fix", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "ishumidity", "Has Humidity", "mdi:water-percent", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "ishumidityinternal", "Internal Humidity", "mdi:home-thermometer", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "is_locked", "Locked", "mdi:lock", EntityCategory.DIAGNOSTIC),
        
        # Additional Sensors (Auxiliary Temperature)
        NetXTextSensor(coordinator, config_entry, "sensor0", "Sensor 0", "mdi:thermometer", None),
        NetXTextSensor(coordinator, config_entry, "sensor1", "Sensor 1", "mdi:thermometer", None),
        NetXTextSensor(coordinator, config_entry, "sensor2", "Sensor 2", "mdi:thermometer", None),
        NetXTextSensor(coordinator, config_entry, "sensor3", "Sensor 3", "mdi:thermometer", None),
        NetXTextSensor(coordinator, config_entry, "sensor4", "Sensor 4", "mdi:thermometer", None),
        NetXTextSensor(coordinator, config_entry, "sensor5", "Sensor 5", "mdi:thermometer", None),
        
        # Time/Day sensors
        NetXTextSensor(coordinator, config_entry, "curday", "Current Day", "mdi:calendar-today", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "curtime", "Current Time", "mdi:clock-outline", EntityCategory.DIAGNOSTIC),
        
        # X7 Sensors - Diagnostic
        NetXTextSensor(coordinator, config_entry, "x7hkhd", "X7 HKHD", "mdi:alpha-x", EntityCategory.DIAGNOSTIC),
        NetXTextSensor(coordinator, config_entry, "x7hk2", "X7 HK2", "mdi:alpha-x", EntityCategory.DIAGNOSTIC),
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
        icon: str,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_entity_category = entity_category
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._sensor_type)
        if value is not None and value != "--":
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        value = self.coordinator.data.get(self._sensor_type)
        return (
            self.coordinator.last_update_success
            and value is not None
            and value != "--"
        )


class NetXTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a NetX Temperature Sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        name: str,
        icon: str,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_entity_category = entity_category
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._sensor_type)
        if value is not None and value != "--":
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        value = self.coordinator.data.get(self._sensor_type)
        return (
            self.coordinator.last_update_success
            and value is not None
            and value != "--"
        )


class NetXHumiditySensor(CoordinatorEntity, SensorEntity):
    """Representation of a NetX Humidity Sensor."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        name: str,
        icon: str,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_entity_category = entity_category
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._sensor_type)
        if value is not None and value != "--":
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        value = self.coordinator.data.get(self._sensor_type)
        return (
            self.coordinator.last_update_success
            and value is not None
            and value != "--"
        )


class NetXTextSensor(CoordinatorEntity, SensorEntity):
    """Representation of a NetX Text Sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        name: str,
        icon: str,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_entity_category = entity_category
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._sensor_type)
        if value is not None and value != "--":
            return str(value).strip()
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        value = self.coordinator.data.get(self._sensor_type)
        return (
            self.coordinator.last_update_success
            and value is not None
            and value != "--"
        )


class NetXManualModeSensor(CoordinatorEntity, SensorEntity):
    """Representation of the Manual/Schedule Mode Sensor."""

    _attr_has_entity_name = True
    _attr_name = "Control Mode"
    _attr_icon = "mdi:cog"

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_control_mode"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        manual_program = self.coordinator.data.get("manual_program")
        if manual_program == "1":
            return "Manual"
        elif manual_program == "0":
            return "Schedule"
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        attrs = {}
        schedstat = self.coordinator.data.get("schedstat")
        if schedstat:
            attrs["schedule_detail"] = schedstat
        schedstat1 = self.coordinator.data.get("schedstat1")
        if schedstat1:
            attrs["schedule_type"] = schedstat1
        return attrs


class NetXScheduleSensor(CoordinatorEntity, SensorEntity):
    """Representation of the Today's Schedule Sensor."""

    _attr_has_entity_name = True
    _attr_name = "Today's Schedule"
    _attr_icon = "mdi:calendar-today"

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_todays_schedule"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    @property
    def native_value(self) -> str | None:
        """Return a summary of today's schedule."""
        curday = self.coordinator.data.get("curday", "").lower()
        schedule = self.coordinator.data.get("schedule", {})
        
        if not curday or curday not in schedule:
            return "No schedule"
        
        today_schedule = schedule.get(curday, [])
        active_count = sum(1 for s in today_schedule if s.get('active', False))
        
        return f"{active_count} active periods"

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes with schedule details."""
        attrs = {}
        curday = self.coordinator.data.get("curday", "").lower()
        schedule = self.coordinator.data.get("schedule", {})
        
        if curday and curday in schedule:
            today_schedule = schedule.get(curday, [])
            for i, sch in enumerate(today_schedule, 1):
                prefix = f"schedule_{i}"
                attrs[f"{prefix}_active"] = sch.get('active', False)
                attrs[f"{prefix}_time"] = sch.get('time', '')
                attrs[f"{prefix}_cool"] = sch.get('cool_setpoint', '')
                attrs[f"{prefix}_heat"] = sch.get('heat_setpoint', '')
                attrs[f"{prefix}_occupancy"] = sch.get('occupancy', '')
                attrs[f"{prefix}_mode"] = sch.get('mode', '')
                attrs[f"{prefix}_fan"] = sch.get('fan', '')
        
        return attrs
