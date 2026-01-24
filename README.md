# NetX Thermostat Integration for Home Assistant

This unofficial custom integration allows you to control and monitor a [NetworkThermostat](https://networkthermostat.com) (NetX) device locally in Home Assistant. 

**Now with official API support! (v3.0)**

## Features

- **Climate Control**
  - Set heating and cooling setpoints (35-90°F)
  - Switch between HEAT, COOL, FAN ONLY, AUTO, and OFF mode
  - View and control fan status (AUTO/ON)
  - Humidification/Dehumidification control
  - Uses the official API that Control4 or RTI integration uses.

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
   - **Host**: The local IP of your thermostat (e.g., 192.168.1.2)
   - **Username**: Your thermostat username
   - **Password**: Your thermostat password
5. Give your thermostat a custom name (e.g., "Living Room Thermostat")

## Troubleshooting

**Cannot connect**: Verify the IP address is correct and the thermostat is reachable on your network.

**Invalid credentials**: Double-check your username and password.

## Notes

- These thermostats aren't typically sold to customers and are quite pricy for the ones with ethernet. (~$600).  Places like [Controls Depot](https://controlsdepot.com) seem to sell direct to consumer however I have not personally confirmed this.
- The devices from [NetworkThermostat](https://networkthermostat.com) are the only ones I am aware of that have local control and **ETHERNET**
- This integration has only been tested with the X7C-IP
- I have not tested other products from NetworkThermostat like the temperature sensors they offer to get a median temperature, so while they *should* work your milage my vary

## Support & Warranty
This repo is not endored or affiliated with NetworkThermostat, NetX or any other party in thereof.  This repo's primary goal is to expand the (albeit borderline nonexistant) userbases' options on how they use their products and what they communicate with.  This repo comes with little support and zero warranty.  You are solely responsible for your usage of the code used in this repository and I take zero responsibility for any damage as a result of anyone using this codebase.
