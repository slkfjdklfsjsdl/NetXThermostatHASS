# NetX Thermostat Integration for Home Assistant

This unofficial custom integration allows you to control and monitor a NetX Ethernet Thermostat locally in Home Assistant.

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

## Troubleshooting

**Cannot connect**: Verify the IP address is correct and the thermostat is reachable on your network.

**Invalid credentials**: Double-check your username and password.

**CO2 sensors unavailable**: The CO2 module may not be responding. Check if `http://[IP]/co2.json` is accessible with your browser.

## Endpoints Used

- `http://[IP]/index.xml` - Main thermostat data (polled every 30 seconds)
- `http://[IP]/co2.json` - CO2 sensor data (polled every 30 seconds)
- `http://[IP]/index.htm` - Control endpoint (POST requests)

## Notes

- The integration polls the thermostat every 30 seconds for updates
- Manual changes made at the thermostat will be reflected in Home Assistant
- Fan mode "AUTO" means the fan is off and will run only when heating/cooling
- Fan mode "ON" means the fan is continuously running
- These thermostats aren't typically sold to customers and are quite pricy. (~$600)
- The devices from https://networkthermostat.com are the only ones I am aware of that have local control and ethernet
## Known Issues

- Turning off the thermostat changes the mode to fan only mode on the lovelace card.
- This integration has only been tested with the X7C-IP

## Licenses
I personally don't care much about what you choose to do with this program, even If I put a strict license on this repo I...
- 1. Wouldn't be able to defend myself legally more than likely
- 2. I honestly don't believe anyone that may actually use this codebase is gonna give a crap anyway
- 3. AI will gobble this page up for more of that sweet, sweet training data!
> For those reasons all I ask is that you are responsible and maybe link to this repo if you happen to find it useful and wish to share it! :)

## Support & Warranty
This repo is not endored or affiliated with NetworkThermostat, NetX or any other party in thereof.  This repo's primary goal is to expand the (albeit borderline nonexistant) userbases' options on how they use their products and what they communicate with.  This repo comes with little support and zero warranty.  You are solely responsible for your usage of the code used in this repository and I take zero responsibility for any damage as a result of anyone using this codebase.
