#!/usr/bin/env python3
"""
Script to generate all NetX Thermostat integration files.
Run this script and it will create a netx_thermostat folder with all files.
"""

import os

# Create the directory
os.makedirs("netx_thermostat", exist_ok=True)

files = {
    "manifest.json": '''{
  "domain": "netx_thermostat",
  "name": "NetX Thermostat",
  "codeowners": [],
  "config_flow": true,
  "documentation": "https://github.com/yourusername/netx_thermostat",
  "integration_type": "device",
  "iot_class": "local_polling",
  "requirements": [],
  "version": "1.0.0"
}''',

    "__init__.py": '''"""The NetX Thermostat integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "netx_thermostat"
PLATFORMS = ["climate", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NetX Thermostat from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
''',

    "config_flow.py": '''"""Config flow for NetX Thermostat integration."""
import logging
import voluptuous as vol
import aiohttp
import xml.etree.ElementTree as ET

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.1.2"): str,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict):
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]

    url = f"http://{host}/index.xml"
    auth = aiohttp.BasicAuth(username, password)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=auth, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 401:
                    raise InvalidAuth
                if response.status != 200:
                    raise CannotConnect
                
                text = await response.text()
                root = ET.fromstring(text)
                isvalid = root.find("isvalid")
                
                if isvalid is None or isvalid.text != "1":
                    raise InvalidAuth
                    
    except aiohttp.ClientError:
        raise CannotConnect
    except ET.ParseError:
        raise CannotConnect

    return {"title": f"NetX Thermostat ({host})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NetX Thermostat."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
''',

    "const.py": '''"""Constants for the NetX Thermostat integration."""

DOMAIN = "netx_thermostat"

# Temperature limits
MIN_TEMP = 64
MAX_TEMP = 86

# Update interval in seconds
UPDATE_INTERVAL = 30
''',

    "climate.py": '''"""Climate platform for NetX Thermostat integration."""
import logging
from datetime import timedelta
import aiohttp
import asyncio
import xml.etree.ElementTree as ET

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
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
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
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
        if mode == "HEAT":
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
''',

    "sensor.py": '''"""Sensor platform for NetX Thermostat integration."""
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
''',

    "strings.json": '''{
  "config": {
    "step": {
      "user": {
        "title": "NetX Thermostat Setup",
        "description": "Enter the connection details for your NetX Thermostat",
        "data": {
          "host": "IP Address",
          "username": "Username",
          "password": "Password"
        }
      }
    },
    "error": {
      "cannot_connect": "Failed to connect to the thermostat. Please check the IP address and try again.",
      "invalid_auth": "Invalid username or password. Please check your credentials.",
      "unknown": "An unexpected error occurred. Please try again."
    },
    "abort": {
      "already_configured": "This thermostat is already configured."
    }
  }
}''',

    "README.md": '''# NetX Thermostat Integration for Home Assistant

This custom integration allows you to control and monitor a NetX Thermostat in Home Assistant version 2025.12.12.

## Features

- **Climate Control**
  - View current temperature
  - View current humidity
  - Set heating and cooling setpoints (64-86°F)
  - Switch between HEAT, COOL, and OFF modes
  - View fan status (AUTO/ON)

- **CO2 Monitoring** (via separate sensors)
  - Current CO2 level
  - Peak CO2 level
  - CO2 alert level

## Installation

1. Create a `custom_components` folder in your Home Assistant config directory if it doesn't exist
2. Create a `netx_thermostat` folder inside `custom_components`
3. Copy all the integration files into the `netx_thermostat` folder:
   - `__init__.py`
   - `manifest.json`
   - `config_flow.py`
   - `const.py`
   - `climate.py`
   - `sensor.py`
   - `strings.json`

Your folder structure should look like:
```
config/
  custom_components/
    netx_thermostat/
      __init__.py
      manifest.json
      config_flow.py
      const.py
      climate.py
      sensor.py
      strings.json
```

4. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "NetX Thermostat"
4. Enter your thermostat details:
   - **IP Address**: The local IP of your thermostat (e.g., 192.168.1.2)
   - **Username**: Your thermostat username (default: admin)
   - **Password**: Your thermostat password

## Usage

Once configured, you'll get:
- A climate entity for thermostat control
- Three sensor entities for CO2 monitoring

The climate entity will show:
- Current temperature and humidity
- Heating and cooling setpoints
- Current HVAC mode
- Fan mode in attributes
- CO2 data in attributes

## Temperature Control

You can control the thermostat through:
- The climate entity card in Lovelace
- Automations and scripts
- Voice assistants (via Home Assistant)

Temperature setpoints are limited to 64-86°F as per the thermostat specifications.

## Troubleshooting

**Cannot connect**: Verify the IP address is correct and the thermostat is reachable on your network.

**Invalid credentials**: Double-check your username and password.

**CO2 sensors unavailable**: The CO2 module may not be responding. Check if `http://[IP]/co2.json` is accessible with your browser.

## API Endpoints Used

- `http://[IP]/index.xml` - Main thermostat data (polled every 30 seconds)
- `http://[IP]/co2.json` - CO2 sensor data (polled every 30 seconds)
- `http://[IP]/index.htm` - Control endpoint (POST requests)

## Notes

- The integration polls the thermostat every 30 seconds for updates
- Manual changes made at the thermostat will be reflected in Home Assistant
- Fan mode "AUTO" means the fan is off and will run only when heating/cooling
- Fan mode "ON" means the fan is continuously running
'''
}

# Write all files
for filename, content in files.items():
    filepath = os.path.join("netx_thermostat", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {filepath}")

print("\n✅ All files created successfully in the 'netx_thermostat' folder!")
print("\nNext steps:")
print("1. Copy the 'netx_thermostat' folder to your Home Assistant 'custom_components' directory")
print("2. Restart Home Assistant")
print("3. Add the integration through Settings → Devices & Services")
