"""Climate platform for NetX Thermostat integration."""
import logging
from datetime import timedelta
import aiohttp
import asyncio
import xml.etree.ElementTree as ET

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, MIN_TEMP, MAX_TEMP, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NetX Thermostat climate platform."""
    host = config_entry.data[CONF_HOST]
    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]

    coordinator = NetXDataUpdateCoordinator(hass, host, username, password)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([NetXClimate(coordinator, config_entry)])


class NetXDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching NetX data."""

    def __init__(self, hass: HomeAssistant, host: str, username: str, password: str):
        """Initialize."""
        self.host = host
        self.username = username
        self.password = password
        self.auth = aiohttp.BasicAuth(username, password)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch index.xml
                xml_url = f"http://{self.host}/index.xml"
                async with session.get(
                    xml_url, auth=self.auth, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Error fetching data: {response.status}")
                    xml_text = await response.text()

                # Fetch co2.json
                co2_url = f"http://{self.host}/co2.json"
                async with session.get(
                    co2_url, auth=self.auth, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        co2_data = None
                    else:
                        co2_data = await response.json()

            # Parse XML
            root = ET.fromstring(xml_text)
            data = {}
            for child in root:
                data[child.tag] = child.text

            # Add CO2 data if available
            if co2_data and "co2" in co2_data:
                data["co2_level"] = co2_data["co2"].get("level")
                data["co2_peak_level"] = co2_data["co2"].get("peak_level")
                data["co2_alert_level"] = co2_data["co2"].get("alert_level")

            return data

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with device: {err}")
        except ET.ParseError as err:
            raise UpdateFailed(f"Error parsing XML: {err}")


class NetXClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a NetX Thermostat."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
    )
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.FAN_ONLY]
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP

    def __init__(self, coordinator: NetXDataUpdateCoordinator, config_entry: ConfigEntry):
        """Initialize the thermostat."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "NetX Thermostat",
            "manufacturer": "NetX",
            "model": "Thermostat",
        }
        self._host = config_entry.data[CONF_HOST]
        self._username = config_entry.data[CONF_USERNAME]
        self._password = config_entry.data[CONF_PASSWORD]

    @property
    def current_temperature(self):
        """Return the current temperature."""
        temp = self.coordinator.data.get("curtemp")
        return float(temp) if temp else None

    @property
    def current_humidity(self):
        """Return the current humidity."""
        humidity = self.coordinator.data.get("humidity")
        return int(humidity) if humidity else None

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        mode = self.hvac_mode
        if mode == HVACMode.HEAT:
            temp = self.coordinator.data.get("sptheat")
        elif mode == HVACMode.COOL:
            temp = self.coordinator.data.get("sptcool")
        else:
            return None
        return float(temp) if temp else None

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature."""
        temp = self.coordinator.data.get("sptcool")
        return float(temp) if temp else None

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature."""
        temp = self.coordinator.data.get("sptheat")
        return float(temp) if temp else None

    @property
    def hvac_mode(self):
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
        else:
            return HVACMode.OFF

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        attrs = {}
        
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
            
        return attrs

    async def async_set_temperature(self, **kwargs):
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
        
        # Handle range setting
        if "target_temp_low" in kwargs:
            temp_low = max(MIN_TEMP, min(MAX_TEMP, kwargs["target_temp_low"]))
            await self._set_heat_setpoint(temp_low)
        
        if "target_temp_high" in kwargs:
            temp_high = max(MIN_TEMP, min(MAX_TEMP, kwargs["target_temp_high"]))
            await self._set_cool_setpoint(temp_high)
        
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.HEAT:
            await self._set_mode("HEAT")
        elif hvac_mode == HVACMode.COOL:
            await self._set_mode("COOL")
        elif hvac_mode == HVACMode.FAN_ONLY:
            await self._set_fan_only()
        elif hvac_mode == HVACMode.OFF:
            await self._set_mode("OFF")
        
        await asyncio.sleep(1)
        await self.coordinator.async_request_refresh()

    async def _set_heat_setpoint(self, temperature: float):
        """Set heating setpoint."""
        url = f"http://{self._host}/index.htm"
        data = {"sp_heat": int(temperature), "update": "Update"}
        auth = aiohttp.BasicAuth(self._username, self._password)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, auth=auth, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to set heat setpoint: %s", response.status)

    async def _set_cool_setpoint(self, temperature: float):
        """Set cooling setpoint."""
        url = f"http://{self._host}/index.htm"
        data = {"sp_cool": int(temperature), "update": "Update"}
        auth = aiohttp.BasicAuth(self._username, self._password)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, auth=auth, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to set cool setpoint: %s", response.status)

    async def _set_mode(self, mode: str):
        """Set thermostat mode."""
        url = f"http://{self._host}/index.htm"
        data = {"mode": mode, "update": "Update"}
        auth = aiohttp.BasicAuth(self._username, self._password)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, auth=auth, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to set mode: %s", response.status)

    async def _set_fan_only(self):
        """Set fan-only mode."""
        url = f"http://{self._host}/index.htm"
        data = {"fan": "ON", "update": "Update"}
        auth = aiohttp.BasicAuth(self._username, self._password)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, auth=auth, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    _LOGGER.error("Failed to set fan-only mode: %s", response.status)
