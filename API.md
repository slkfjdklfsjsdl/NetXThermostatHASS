# NetX Thermostat TCP API Documentation

This document describes the TCP socket API used by NetX Network Thermostats. This API is used by professional integrations (Control4, RTI, etc.) and provides real-time control of the thermostat.

## Connection Details

| Parameter | Value |
|-----------|-------|
| Protocol | TCP Socket |
| Default Port | 10001 |
| Line Ending | `\r\n` (CRLF) |
| Encoding | ASCII |

## Authentication

### Login Command

```
WMLS1D{username},{base64_hash}
```

Where `base64_hash` is generated as:
```python
import hashlib
import base64

auth_string = f"{username}:{password}"
sha256_hash = hashlib.sha256(auth_string.encode()).digest()
base64_hash = base64.b64encode(sha256_hash).decode()
```

### Login Response

| Response | Meaning |
|----------|---------|
| `OK,USER,NO` | Success (standard user) |
| `OK,ADMIN,NO` | Success (admin user) |
| `ERROR` | Authentication failed |

---

## Read Commands

All read commands follow the pattern: `R{COMMAND}1` and return `R{COMMAND}1:{value}`

### RAS1 - Read All States (Primary Command)

**Command:** `RAS1`

**Response Format:**
```
RAS1:{indoor_temp},{outdoor_temp},{hvac_mode},{fan_mode},{override},{recovery},{cool_sp},{heat_sp},{op_status},{stage},{event}
```

**Example:**
```
RAS1:70,NA,HEAT,FAN AUTO,NO,NO,77,68,HEAT,1,NONE
```

**Fields:**

| Position | Field | Values | Description |
|----------|-------|--------|-------------|
| 0 | Indoor Temp | Number or `NA` | Current indoor temperature |
| 1 | Outdoor Temp | Number or `NA` | Outdoor temperature (if sensor connected) |
| 2 | HVAC Mode | `OFF`, `HEAT`, `COOL`, `AUTO` | Current thermostat mode |
| 3 | Fan Mode | `FAN AUTO`, `FAN ON` | Fan setting |
| 4 | Override | `YES`, `NO` | Schedule override active |
| 5 | Recovery | `YES`, `NO` | Recovery mode active |
| 6 | Cool Setpoint | Number | Cooling setpoint |
| 7 | Heat Setpoint | Number | Heating setpoint |
| 8 | Operating Status | `OFF`, `HEAT`, `COOL` | What's currently running |
| 9 | Stage | `0`, `1`, `2`, `3` | Current stage (0=idle) |
| 10 | Event | `NONE` or event name | Current event |

**Idle Detection:**
- `Stage = 0` means the thermostat is at setpoint (idle)
- `Stage >= 1` means actively heating/cooling

### RTS1 - Read Temperature Scale

**Command:** `RTS1`

**Response:** `RTS1:FAHRENHEIT` or `RTS1:CELSIUS`

### RRHS1 - Read Room Humidity

**Command:** `RRHS1`

**Response:** `RRHS1:{humidity_percent}`

### RNS1 - Read Operation Mode (Manual/Schedule)

**Command:** `RNS1`

**Response:**
- `RNS1:ON` - Manual mode is ON
- `RNS1:OFF` - Manual mode is OFF (Schedule mode)

### RMRF1 - Read Humidity Relay Mode

**Command:** `RMRF1`

**Response:** `RMRF1:{relay1_mode},{relay2_mode}`

**Values:** `OFF`, `HUM`, `DEHUM`

**Example:** `RMRF1:OFF,OFF`

### RMHS1 - Read Humidification Settings

**Command:** `RMHS1`

**Response:** `RMHS1:{mode},{setpoint},{variance}`

**Mode Values:**
- `WH` - With Heating (runs only when heating is active)
- `IH` - Independent of Heating (runs independently)

**Example:** `RMHS1:WH,50,5` (With Heating, 50% setpoint, ±5% variance)

### RMDHS1 - Read Dehumidification Settings

**Command:** `RMDHS1`

**Response:** `RMDHS1:{mode},{setpoint},{variance}`

**Mode Values:**
- `WC` - With Cooling (runs only when cooling is active)
- `IC` - Independent of Cooling (runs independently)

**Example:** `RMDHS1:IC,55,5` (Independent of Cooling, 55% setpoint, ±5% variance)

### RRS1 - Read Relay State

**Command:** `RRS1`

**Response:** `RRS1:{state}`

**Example:** `RRS1:OFF`

### RSS1 - Read System State

**Command:** `RSS1`

**Response:** `RSS1:{mode},{stage}`

**Example:** `RSS1:HEAT,1` (Heating, Stage 1)

### ROC1 - Read Occupied Cool Setpoint

**Command:** `ROC1`

**Response:** `ROC1:{temperature}`

### RCS1 - Read Cool Stages

**Command:** `RCS1`

**Response:** `RCS1:{stage_config}`

**Example:** `RCS1:MAN2` (Manual 2-stage)

---

## Write Commands

Write commands follow different patterns based on whether the thermostat is in Manual or Schedule mode.

### Response Format

Successful write commands echo the command with the set value:
```
{COMMAND}:{value_set}
```

**Example:** `WNHD1D70:70` (Heat setpoint set to 70)

### Manual Mode Commands (WN prefix)

These commands are used when `RNS1` returns `ON` (manual mode):

| Command | Format | Description |
|---------|--------|-------------|
| `WNMS1D` | `WNMS1D{OFF\|HEAT\|COOL\|AUTO}` | Set HVAC mode |
| `WNFM1D` | `WNFM1D{AUTO\|ON}` | Set fan mode |
| `WNHD1D` | `WNHD1D{temp}` | Set heat setpoint |
| `WNCD1D` | `WNCD1D{temp}` | Set cool setpoint |

**Examples:**
```
WNMS1DHEAT     → WNMS1DHEAT:HEAT
WNFM1DON       → WNFM1DON:ON
WNHD1D70       → WNHD1D70:70
WNCD1D75       → WNCD1D75:75
```

### Schedule Mode Commands (W prefix, no N)

These commands are used when `RNS1` returns `OFF` (schedule mode):

| Command | Format | Description |
|---------|--------|-------------|
| `WMS1D` | `WMS1D{OFF\|HEAT\|COOL\|AUTO}` | Set HVAC mode |
| `WFM1D` | `WFM1D{AUTO\|ON}` | Set fan mode |
| `WOH1D` | `WOH1D{temp}` | Override heat setpoint |
| `WOC1D` | `WOC1D{temp}` | Override cool setpoint |

### General Write Commands

These work regardless of manual/schedule mode:

| Command | Format | Description |
|---------|--------|-------------|
| `WTS1D` | `WTS1D{F\|C}` | Set temperature scale |
| `WMRF1D` | `WMRF1D{OFF\|HUM\|DEHUM}` | Set humidity relay mode |
| `WMHS1D` | `WMHS1D{IH\|WH},{setpoint},{variance}` | Set humidification |
| `WMDHS1D` | `WMDHS1D{IC\|WC},{setpoint},{variance}` | Set dehumidification |

**Humidification Examples:**
```
WMHS1DIH,45,5   → Independent of Heating, 45%, ±5%
WMHS1DWH,50,3   → With Heating, 50%, ±3%
```

**Dehumidification Examples:**
```
WMDHS1DIC,55,5  → Independent of Cooling, 55%, ±5%
WMDHS1DWC,60,3  → With Cooling, 60%, ±3%
```

---

## Command Summary Table

### Read Commands

| Command | Description | Example Response |
|---------|-------------|------------------|
| `RTS1` | Temperature scale | `RTS1:FAHRENHEIT` |
| `RAS1` | All states | `RAS1:70,NA,HEAT,FAN AUTO,NO,NO,77,68,HEAT,1,NONE` |
| `RRHS1` | Room humidity | `RRHS1:0` |
| `RNS1` | Manual/Schedule mode | `RNS1:ON` |
| `RMRF1` | Humidity relay mode | `RMRF1:OFF,OFF` |
| `RMHS1` | Humidification settings | `RMHS1:WH,50,5` |
| `RMDHS1` | Dehumidification settings | `RMDHS1:IC,55,5` |
| `RRS1` | Relay state | `RRS1:OFF` |
| `RSS1` | System state | `RSS1:HEAT,1` |
| `ROC1` | Occupied cool setpoint | `ROC1:77` |
| `RCS1` | Cool stages | `RCS1:MAN2` |

### Write Commands (Manual Mode)

| Command | Description | Example |
|---------|-------------|---------|
| `WNMS1D{mode}` | Set HVAC mode | `WNMS1DHEAT` |
| `WNFM1D{mode}` | Set fan mode | `WNFM1DON` |
| `WNHD1D{temp}` | Set heat setpoint | `WNHD1D70` |
| `WNCD1D{temp}` | Set cool setpoint | `WNCD1D75` |

### Write Commands (Schedule Mode)

| Command | Description | Example |
|---------|-------------|---------|
| `WMS1D{mode}` | Set HVAC mode | `WMS1DHEAT` |
| `WFM1D{mode}` | Set fan mode | `WFM1DON` |
| `WOH1D{temp}` | Override heat setpoint | `WOH1D70` |
| `WOC1D{temp}` | Override cool setpoint | `WOC1D75` |

### Write Commands (General)

| Command | Description | Example |
|---------|-------------|---------|
| `WTS1D{scale}` | Set temp scale | `WTS1DF` |
| `WMRF1D{mode}` | Set humidity relay | `WMRF1DHUM` |
| `WMHS1D{m},{sp},{var}` | Set humidification | `WMHS1DWH,50,5` |
| `WMDHS1D{m},{sp},{var}` | Set dehumidification | `WMDHS1DIC,55,5` |

---

## Error Responses

| Response | Meaning |
|----------|---------|
| `BAD COMMAND` | Command not recognized |
| `ERROR` | General error |
| `?` | Unknown command |

---

## Notes

1. **Session Management:** The TCP connection can be kept open for continuous communication. Re-authentication is required if the connection drops.

2. **Polling:** Unlike push notifications, you must poll for state changes. A 10-30 second interval is recommended.

3. **Humidity Sensor:** Humidity readings are not available via the TCP API. Use the HTTP API (`/index.xml`) to read humidity.

4. **CO2 Sensor:** CO2 readings are not available via TCP API. Use the HTTP API (`/co2.json`) for CO2 data.

5. **Temperature Limits:**
   - Heat setpoint: 35-89°F
   - Cool setpoint: 42-90°F

6. **Humidity Limits:**
   - Setpoint: 10-90%
   - Variance: 2-10%

---

## HTTP Endpoints (For Reference)

The thermostat also exposes an HTTP API for additional features not available via TCP:

| Endpoint | Description |
|----------|-------------|
| `/index.xml` | Main status XML |
| `/co2.json` | CO2 and humidity sensor data |
| `/schedule.xml` | Weekly schedule data |
| `/confighumidity.htm` | Humidity configuration |

### /index.xml

Returns XML with thermostat status including humidity:

```xml
<?xml version="1.0"?>
<thermostat>
  <temperature>70</temperature>
  <humidity>25</humidity>
  <mode>HEAT</mode>
  ...
</thermostat>
```

The `<humidity>` element contains the current indoor humidity percentage.

### /co2.json

Returns JSON with CO2 sensor data (if CO2 module installed):

```json
{
  "co2": {
    "type": "MODULE",
    "valid": "true",
    "in_alert": "false",
    "level": "635",
    "peak_level": "1067",
    "peak_reset": "MANUAL",
    "alert_level": "1100",
    "display": "CURRENT",
    "relay_high": "false",
    "relay_failure": "false"
  }
}
```

**Fields:**
- `level`: Current CO2 level in PPM (typical range: 400-2000)
- `peak_level`: Peak CO2 level since last reset
- `alert_level`: Threshold for CO2 alert
- `in_alert`: Whether currently in alert state ("true"/"false")
- `valid`: Whether the sensor data is valid ("true"/"false")
- `peak_reset`: When peak resets ("MANUAL" or time-based)

**Note:** Returns 404 if no CO2 module is installed. All numeric values are strings.

---

## Python Example

```python
import socket
import hashlib
import base64

def connect_thermostat(host, port, username, password):
    # Generate auth hash
    auth_string = f"{username}:{password}"
    sha256_hash = hashlib.sha256(auth_string.encode()).digest()
    base64_hash = base64.b64encode(sha256_hash).decode()
    
    # Connect
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((host, port))
    
    # Authenticate
    login_cmd = f"WMLS1D{username},{base64_hash}\r\n"
    sock.send(login_cmd.encode())
    response = sock.recv(1024).decode().strip()
    
    if not response.startswith("OK"):
        raise Exception(f"Authentication failed: {response}")
    
    return sock

def send_command(sock, command):
    sock.send(f"{command}\r\n".encode())
    return sock.recv(1024).decode().strip()

# Usage
sock = connect_thermostat("192.168.1.100", 10001, "admin", "password")
print(send_command(sock, "RAS1"))  # Get all states
print(send_command(sock, "WNHD1D72"))  # Set heat to 72
sock.close()
```

---

## Changelog

- **v1.0** - Initial documentation based on reverse engineering Control4/RTI drivers and testing
