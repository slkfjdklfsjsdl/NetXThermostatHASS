"""Constants for the NetX Thermostat integration."""

DOMAIN = "netx_thermostat"

# Temperature limits (expanded based on official drivers)
MIN_TEMP_HEAT = 35
MAX_TEMP_HEAT = 89
MIN_TEMP_COOL = 42
MAX_TEMP_COOL = 90

# Legacy limits for general use
MIN_TEMP = 35
MAX_TEMP = 90

# Update interval in seconds
UPDATE_INTERVAL = 10

# Humidity relay modes
RELAY_MODE_OFF = 0
RELAY_MODE_DAMPER = 1
RELAY_MODE_DEHUMIDIFY = 2
RELAY_MODE_HUMIDIFY = 3
RELAY_MODE_MANUAL = 4
RELAY_MODE_SCHEDULE = 5
RELAY_MODE_IAQ = 6
RELAY_MODE_CO2 = 7

RELAY_MODES = {
    RELAY_MODE_OFF: "Off",
    RELAY_MODE_DAMPER: "Damper",
    RELAY_MODE_DEHUMIDIFY: "Dehumidify",
    RELAY_MODE_HUMIDIFY: "Humidify",
    RELAY_MODE_MANUAL: "Manual",
    RELAY_MODE_SCHEDULE: "Schedule",
    RELAY_MODE_IAQ: "IAQ",
    RELAY_MODE_CO2: "CO2",
}

RELAY_MODES_REVERSE = {v: k for k, v in RELAY_MODES.items()}

# Humidity control modes (for reference)
# 0 = With HVAC (dehumidify runs with cooling, humidify runs with heating)
# 1 = Independent (runs regardless of heating/cooling)

# Endpoints
ENDPOINT_INDEX_XML = "/index.xml"
ENDPOINT_INDEX_HTM = "/index.htm"
ENDPOINT_CO2_JSON = "/co2.json"
ENDPOINT_CONFIG_HUMIDITY = "/confighumidity.htm"
ENDPOINT_REBOOT = "/reboot.htm"
ENDPOINT_SCHEDULE_XML = "/schedule.xml"
ENDPOINT_SCHEDULE_HTM = "/schedule.htm"
