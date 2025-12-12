# NetX Thermostat Integration for Home Assistant

This unofficial custom integration allows you to control and monitor a [NetworkThermostat](https://networkthermostat.com) (NetX) device locally in Home Assistant.

## Features

- **Climate Control**
  - View current temperature
  - View current humidity
  - Set heating and cooling setpoints (64-86°F)
  - Switch between HEAT, COOL, FAN ONLY, and OFF modes
  - View fan status (AUTO/ON)
  - Real-time HVAC action status (actively heating, cooling, fan, or idle)

- **Restart Button**
  - Remotely restart/reboot the thermostat

- **CO2 Monitoring Sensors**
  - CO2 Level (ppm)
  - CO2 Peak Level (ppm)
  - CO2 Alert Level (ppm)
  - CO2 Type
  - CO2 Valid Status
  - CO2 In Alert Status
  - CO2 Peak Reset Mode
  - CO2 Display Mode
  - CO2 Relay High Status
  - CO2 Relay Failure Status

- **Temperature Sensors**
  - Outdoor Temperature
  - Occupied/Unoccupied Cool/Heat Setpoint Limits

- **Humidity Sensors**
  - Indoor / Outdoor Humidity

- **Schedule & Program Sensors**
  - Manual Program Status
  - Current Schedule
  - Schedule Status
  - Override Status

- **System Status Sensors**
  - System Adapt Status
  - Humidity Sensor Status
  - Lock Status
  - ind0, ind1, ind2

- **Additional Sensors**
  - 6 configurable sensor inputs (sensor0-5)
  - X7 system sensors (no idea what these are to be honest)

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
5. **Step 2**: After successful connection, give your thermostat a custom name (e.g., "Living Room Thermostat")

## Usage

Once configured, you'll get:
- **1 Climate entity** for thermostat control
- **1 Button entity** for restarting the thermostat
- **70+ sensor entities** for comprehensive monitoring

The climate entity will show:
- Current temperature and humidity
- Heating and cooling setpoints
- Current HVAC mode (Heat/Cool/Fan Only/Off)
- Current HVAC action (Heating/Cooling/Fan/Idle)
- Fan mode in attributes
- CO2 data in attributes

### Sensor Categories

**CO2 Sensors** - Monitor air quality
**Temperature Sensors** - Indoor, outdoor, and setpoint limits
**Humidity Sensors** - Indoor and outdoor humidity
**Schedule Sensors** - Programming and schedule status
**Raw Sensors** - Raw values from all connected sensors
**Restart Button** - Restart the thermostat from Home Assistant

### Unavailable Sensors

Sensors that report "--" in the thermostat data will show as "unavailable" in Home Assistant. This is normal for sensors that are not configured or connected.

## Troubleshooting

**Cannot connect**: Verify the IP address is correct and the thermostat is reachable on your network.

**Invalid credentials**: Double-check your username and password.

**CO2 sensors unavailable**: The CO2 module may not be responding. Check if `http://[IP]/co2.json` is accessible with your browser.

## API Endpoints Used

- `http://[IP]/index.xml` - Main thermostat data (polled every 30 seconds)
- `http://[IP]/co2.json` - CO2 sensor data (polled every 30 seconds)
- `http://[IP]/index.htm` - Control endpoint (POST requests)
- `http://[IP]/reboot.htm` - Restart/reboot endpoint (GET request)

## Notes

- The integration polls the thermostat every 30 seconds for updates
- Manual changes made at the thermostat will be reflected in Home Assistant
- Fan mode "AUTO" means the fan is off and will run only when heating/cooling
- Fan mode "ON" means the fan is continuously running
- These thermostats aren't typically sold to customers and are quite pricy for the ones with ethernet. (~$600).  Places like [Controls Depot](https://controlsdepot.com) seem to sell direct to consumer however I have not personally confirmed this.
- The devices from [NetworkThermostat](https://networkthermostat.com) are the only ones I am aware of that have local control and **ETHERNET**
- This integration has only been tested with the X7C-IP
- The schedules tab on the device is unlikely to be added to this integration as you should probably use Home Assistant's native automations for that.
- I have not tested other products from NetworkThermostat like the temperature sensors they offer to get a median temperature, so while they *should* would your milage my vary

## Licenses
I personally don't care much about what you choose to do with this program, even If I put a strict license on this repo I...
- 1. Wouldn't be able to defend myself legally more than likely
- 2. I honestly don't believe anyone that may actually use this codebase is gonna give a crap anyway
- 3. AI will gobble this page up for more of that sweet, sweet training data!
> For those reasons all I ask is that you are responsible and maybe link to this repo if you happen to find it useful and wish to share it! :)

## Support & Warranty
This repo is not endored or affiliated with NetworkThermostat, NetX or any other party in thereof.  This repo's primary goal is to expand the (albeit borderline nonexistant) userbases' options on how they use their products and what they communicate with.  This repo comes with little support and zero warranty.  You are solely responsible for your usage of the code used in this repository and I take zero responsibility for any damage as a result of anyone using this codebase.
