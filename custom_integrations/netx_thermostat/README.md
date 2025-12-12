# NetX Thermostat Integration for Home Assistant

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
