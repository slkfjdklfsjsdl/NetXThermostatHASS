"""Constants for the NetX Thermostat integration."""

DOMAIN = "netx_thermostat"

# Default connection settings
DEFAULT_PORT = 10001
CONNECTION_TIMEOUT = 10
COMMAND_TIMEOUT = 5

# Update interval in seconds
UPDATE_INTERVAL = 30

# Temperature limits (based on official drivers)
MIN_TEMP_HEAT = 35
MAX_TEMP_HEAT = 89
MIN_TEMP_COOL = 42
MAX_TEMP_COOL = 90
MIN_TEMP = 35
MAX_TEMP = 90

# Humidity limits
MIN_HUMIDITY_SETPOINT = 10
MAX_HUMIDITY_SETPOINT = 90
MIN_HUMIDITY_VARIANCE = 2
MAX_HUMIDITY_VARIANCE = 10

# API Commands - Read
CMD_LOGIN = "WMLS1D"  # Login: WMLS1D{username},{base64_hash}
CMD_GET_TEMP_SCALE = "RTS1"  # Get temperature scale
CMD_GET_ALL_STATES = "RAS1"  # Get all thermostat states
CMD_GET_HUMIDITY = "RRHS1"  # Get room humidity
CMD_GET_OPERATION_MODE = "RNS1"  # Get manual/schedule mode (ON=manual, OFF=schedule)
CMD_GET_RELAY_MODE = "RMRF1"  # Get humidity relay mode -> RMRF1:OFF,OFF or RMRF1:HUM,OFF etc.
CMD_GET_HUMIDIFICATION = "RMHS1"  # Get humidification -> RMHS1:WH,50,5 (mode,setpoint,variance)
CMD_GET_DEHUMIDIFICATION = "RMDHS1"  # Get dehumidification -> RMDHS1:IC,55,5 (mode,setpoint,variance)
CMD_GET_RELAY_STATE = "RRS1"  # Get relay state -> RRS1:OFF
CMD_GET_OCCUPIED_COOL = "ROC1"  # Get occupied cool setpoint -> ROC1:77
CMD_GET_COOL_STAGES = "RCS1"  # Get cool stages -> RCS1:MAN2

# API Commands - Write (Manual Mode - WN prefix)
CMD_SET_MODE_MANUAL = "WNMS1D"  # Set HVAC mode in manual: WNMS1D{OFF|HEAT|COOL|AUTO}
CMD_SET_FAN_MANUAL = "WNFM1D"  # Set fan mode in manual: WNFM1D{AUTO|ON}
CMD_SET_COOL_MANUAL = "WNCD1D"  # Set cool setpoint in manual: WNCD1D{temp}
CMD_SET_HEAT_MANUAL = "WNHD1D"  # Set heat setpoint in manual: WNHD1D{temp}

# API Commands - Write (Schedule Mode - W prefix without N)
CMD_SET_MODE_SCHEDULE = "WMS1D"  # Set HVAC mode in schedule: WMS1D{OFF|HEAT|COOL|AUTO}
CMD_SET_FAN_SCHEDULE = "WFM1D"  # Set fan mode in schedule: WFM1D{AUTO|ON}
CMD_SET_COOL_SCHEDULE = "WOC1D"  # Set cool setpoint override: WOC1D{temp}
CMD_SET_HEAT_SCHEDULE = "WOH1D"  # Set heat setpoint override: WOH1D{temp}

# API Commands - Write (General)
CMD_SET_TEMP_SCALE = "WTS1D"  # Set temperature scale: WTS1D{F|C}

# API Commands - Write (Humidity)
CMD_SET_RELAY_MODE = "WMRF1D"  # Set humidity relay mode: WMRF1D{OFF|HUM|DEHUM}
CMD_SET_HUMIDIFICATION = "WMHS1D"  # Set humidification: WMHS1D{IH|WH},{setpoint},{variance}
CMD_SET_DEHUMIDIFICATION = "WMDHS1D"  # Set dehumidification: WMDHS1D{IC|WC},{setpoint},{variance}

# HVAC Modes
HVAC_MODE_OFF = "OFF"
HVAC_MODE_HEAT = "HEAT"
HVAC_MODE_COOL = "COOL"
HVAC_MODE_AUTO = "AUTO"

# Fan Modes
FAN_MODE_AUTO = "AUTO"
FAN_MODE_ON = "ON"

# Operation Modes (Manual vs Schedule)
OPERATION_MODE_MANUAL = "ON"  # RNS1:ON means manual mode is ON
OPERATION_MODE_SCHEDULE = "OFF"  # RNS1:OFF means manual mode is OFF (schedule mode)

# Humidity Control Modes
HUMIDITY_WITH_HEATING = "WH"  # Humidification runs with heating
HUMIDITY_INDEPENDENT_HEATING = "IH"  # Humidification runs independently of heating
HUMIDITY_WITH_COOLING = "WC"  # Dehumidification runs with cooling
HUMIDITY_INDEPENDENT_COOLING = "IC"  # Dehumidification runs independently of cooling

# Humidity Relay Modes
RELAY_MODE_OFF = "OFF"
RELAY_MODE_HUM = "HUM"
RELAY_MODE_DEHUM = "DEHUM"

# Response prefixes
RESP_LOGIN_OK = "OK"
RESP_TEMP_SCALE = "RTS1:"
RESP_ALL_STATES = "RAS1:"
RESP_HUMIDITY = "RRHS1:"
RESP_OPERATION_MODE = "RNS1:"
RESP_RELAY_MODE = "RMRF1:"
RESP_HUMIDIFICATION = "RMHS1:"
RESP_DEHUMIDIFICATION = "RMDHS1:"
RESP_RELAY_STATE = "RRS1:"
