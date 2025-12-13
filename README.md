# NetX Thermostat Integration for Home Assistant

This unofficial custom integration allows you to control and monitor a [NetworkThermostat](https://networkthermostat.com) (NetX) device locally in Home Assistant.

## Features

- **Climate Control**
  - View current temperature
  - View current humidity
  - Set heating and cooling setpoints (60-88°F)
  - Switch between HEAT, COOL, FAN ONLY, and OFF modes
  - View fan status (AUTO/ON)
  - Real-time HVAC action status (actively heating, cooling, fan, or idle)

## Installation

- **Via HACS**
1. Install this repo via HACS by copying the link into the custom repos option
2. Restart Home Assistant
- **Manual Installation**
1. Manual install requires copying the custom_components folder into your Home Assistant installation.
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "NetX Thermostat"
4. Enter your thermostat details:
   - **IP Address**: The local IP of your thermostat (e.g., 192.168.1.2)
   - **Username**: Your thermostat username
   - **Password**: Your thermostat password
5. After successful connection, give your thermostat a custom name (e.g., "Living Room Thermostat")

### Sensor Categories

- **CO2 Sensors** - Monitor air quality
- **Temperature Sensors** - Indoor, outdoor, and setpoint limits
- **Humidity Sensors** - Indoor and outdoor humidity
- **Schedule Sensors** - Programming and schedule status
- **Raw Sensors** - Raw values from all connected sensors
- **Restart Button** - Restart the thermostat from Home Assistant

### Unavailable Sensors

Sensors that report "--" in the thermostat data will show as "unavailable" in Home Assistant. This is normal for sensors that are not configured or connected.

## Troubleshooting

**Cannot connect**: Verify the IP address is correct and the thermostat is reachable on your network.

**Invalid credentials**: Double-check your username and password.

**CO2 sensors unavailable**: The CO2 module may not be responding. Check if `http://[IP]/co2.json` is accessible with your browser.

## API Endpoints Used

- `http://[IP]/index.xml` - Main thermostat data (polled every 10 seconds)
- `http://[IP]/co2.json` - CO2 sensor data (polled every 10 seconds)
- `http://[IP]/index.htm` - Control endpoint (POST requests)
- `http://[IP]/reboot.htm` - Restart/reboot endpoint (GET request)

## Notes

- The integration polls the thermostat every 30 seconds for updates
- These thermostats aren't typically sold to customers and are quite pricy for the ones with ethernet. (~$600).  Places like [Controls Depot](https://controlsdepot.com) seem to sell direct to consumer however I have not personally confirmed this.
- The devices from [NetworkThermostat](https://networkthermostat.com) are the only ones I am aware of that have local control and **ETHERNET**
- This integration has only been tested with the X7C-IP
- The schedules tab on the device is unlikely to be added to this integration as you should probably use Home Assistant's native automations for that.
- I have not tested other products from NetworkThermostat like the temperature sensors they offer to get a median temperature, so while they *should* would your milage my vary

## Support & Warranty
This repo is not endored or affiliated with NetworkThermostat, NetX or any other party in thereof.  This repo's primary goal is to expand the (albeit borderline nonexistant) userbases' options on how they use their products and what they communicate with.  This repo comes with little support and zero warranty.  You are solely responsible for your usage of the code used in this repository and I take zero responsibility for any damage as a result of anyone using this codebase.
