"""NetX Thermostat TCP API Client with HTTP sensor support."""
import asyncio
import hashlib
import base64
import logging
import re
import aiohttp
from dataclasses import dataclass

from .const import (
    DEFAULT_PORT,
    CONNECTION_TIMEOUT,
    COMMAND_TIMEOUT,
    CMD_LOGIN,
    CMD_GET_TEMP_SCALE,
    CMD_GET_ALL_STATES,
    CMD_GET_OPERATION_MODE,
    CMD_GET_RELAY_MODE,
    CMD_GET_HUMIDIFICATION,
    CMD_GET_DEHUMIDIFICATION,
    CMD_GET_RELAY_STATE,
    CMD_SET_MODE_MANUAL,
    CMD_SET_MODE_SCHEDULE,
    CMD_SET_FAN_MANUAL,
    CMD_SET_FAN_SCHEDULE,
    CMD_SET_COOL_MANUAL,
    CMD_SET_COOL_SCHEDULE,
    CMD_SET_HEAT_MANUAL,
    CMD_SET_HEAT_SCHEDULE,
    CMD_SET_RELAY_MODE,
    CMD_SET_HUMIDIFICATION,
    CMD_SET_DEHUMIDIFICATION,
    RESP_LOGIN_OK,
    RESP_TEMP_SCALE,
    RESP_ALL_STATES,
    RESP_OPERATION_MODE,
    RESP_RELAY_MODE,
    RESP_HUMIDIFICATION,
    RESP_DEHUMIDIFICATION,
    RESP_RELAY_STATE,
    OPERATION_MODE_MANUAL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class NetXThermostatState:
    """Representation of thermostat state from TCP API."""
    
    # Basic state from RAS1
    indoor_temp: float | None = None
    outdoor_temp: float | None = None
    hvac_mode: str | None = None
    fan_mode: str | None = None
    override_active: bool = False
    recovery_active: bool = False
    cool_setpoint: int | None = None
    heat_setpoint: int | None = None
    operating_status: str | None = None
    stage: int | None = None
    event: str | None = None
    
    # Derived state
    is_idle: bool = True  # True when stage=0
    
    # From other commands
    temp_scale: str = "F"
    is_manual_mode: bool = True
    operation_mode: str = "Manual"
    
    # Humidity relay
    relay1_mode: str | None = None
    relay2_mode: str | None = None
    relay_state: str | None = None
    
    # Humidification settings
    hum_control_mode: str | None = None
    hum_setpoint: int | None = None
    hum_variance: int | None = None
    
    # Dehumidification settings
    dehum_control_mode: str | None = None
    dehum_setpoint: int | None = None
    dehum_variance: int | None = None
    
    # HTTP-sourced sensor data
    humidity: int | None = None  # From index.xml
    co2_level: int | None = None  # From co2.json
    co2_peak_level: int | None = None  # Peak CO2 from co2.json
    co2_alert_level: int | None = None  # Alert threshold
    co2_in_alert: bool = False  # Currently in alert state
    
    # Connection status
    connected: bool = False
    last_error: str | None = None


class NetXThermostatAPI:
    """TCP API client for NetX Thermostat with HTTP sensor support."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = DEFAULT_PORT,
    ) -> None:
        """Initialize the API client."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        # TCP connection
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._authenticated = False
        
        # HTTP session for sensor data
        self._http_session: aiohttp.ClientSession | None = None
        self._http_auth = aiohttp.BasicAuth(username, password)
        
        self.state = NetXThermostatState()

    def _generate_auth_hash(self) -> str:
        """Generate the authentication hash."""
        auth_string = f"{self.username}:{self.password}"
        sha256_hash = hashlib.sha256(auth_string.encode()).digest()
        return base64.b64encode(sha256_hash).decode()

    async def connect(self) -> bool:
        """Connect and authenticate with the thermostat."""
        try:
            async with self._lock:
                await self._close_connection_locked()
                
                _LOGGER.debug("Connecting to %s:%s", self.host, self.port)
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=CONNECTION_TIMEOUT
                )
                
                auth_hash = self._generate_auth_hash()
                login_cmd = f"{CMD_LOGIN}{self.username},{auth_hash}\r\n"
                
                self._writer.write(login_cmd.encode())
                await self._writer.drain()
                
                response = await asyncio.wait_for(
                    self._reader.readline(),
                    timeout=COMMAND_TIMEOUT
                )
                response_str = response.decode().strip()
                
                if response_str.startswith(RESP_LOGIN_OK):
                    self._authenticated = True
                    self.state.connected = True
                    self.state.last_error = None
                    _LOGGER.info("Connected to NetX Thermostat at %s", self.host)
                    return True
                else:
                    self._authenticated = False
                    self.state.connected = False
                    self.state.last_error = f"Authentication failed: {response_str}"
                    _LOGGER.error("Authentication failed: %s", response_str)
                    return False
                    
        except asyncio.TimeoutError:
            self.state.connected = False
            self.state.last_error = "Connection timeout"
            _LOGGER.error("Connection timeout to %s:%s", self.host, self.port)
            return False
        except OSError as err:
            self.state.connected = False
            self.state.last_error = f"Connection failed: {err}"
            _LOGGER.error("Connection error: %s", err)
            return False
        except Exception as err:
            self.state.connected = False
            self.state.last_error = str(err)
            _LOGGER.error("Unexpected error: %s", err)
            return False

    async def _close_connection_locked(self) -> None:
        """Close connection (must hold lock)."""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None
        self._authenticated = False

    async def disconnect(self) -> None:
        """Disconnect from the thermostat."""
        async with self._lock:
            await self._close_connection_locked()
            self.state.connected = False
        
        # Close HTTP session
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None

    async def _send_command(self, command: str) -> str | None:
        """Send a command and receive response."""
        if not self._authenticated:
            if not await self.connect():
                return None
        
        try:
            async with self._lock:
                if not self._writer or not self._reader:
                    return None
                
                self._writer.write(f"{command}\r\n".encode())
                await self._writer.drain()
                
                response = await asyncio.wait_for(
                    self._reader.readline(),
                    timeout=COMMAND_TIMEOUT
                )
                response_str = response.decode().strip()
                
                _LOGGER.debug("Command: %s -> %s", command, response_str)
                return response_str
                
        except asyncio.TimeoutError:
            _LOGGER.warning("Command timeout: %s", command)
            self._authenticated = False
            self.state.connected = False
            return None
        except Exception as err:
            _LOGGER.error("Command error: %s - %s", command, err)
            self._authenticated = False
            self.state.connected = False
            return None

    async def async_update(self) -> NetXThermostatState:
        """Fetch all data from the thermostat."""
        try:
            # === TCP API DATA ===
            
            # Temperature scale
            response = await self._send_command(CMD_GET_TEMP_SCALE)
            if response and response.startswith(RESP_TEMP_SCALE):
                scale = response.replace(RESP_TEMP_SCALE, "").strip()
                self.state.temp_scale = "F" if "FAHRENHEIT" in scale.upper() else "C"
            
            # All states (main data)
            response = await self._send_command(CMD_GET_ALL_STATES)
            if response and response.startswith(RESP_ALL_STATES):
                self._parse_all_states(response.replace(RESP_ALL_STATES, ""))
            
            # Operation mode (manual vs schedule)
            response = await self._send_command(CMD_GET_OPERATION_MODE)
            if response and response.startswith(RESP_OPERATION_MODE):
                mode = response.replace(RESP_OPERATION_MODE, "").strip()
                self.state.is_manual_mode = (mode == OPERATION_MODE_MANUAL)
                self.state.operation_mode = "Manual" if self.state.is_manual_mode else "Schedule"
            
            # Humidity relay mode
            response = await self._send_command(CMD_GET_RELAY_MODE)
            if response and response.startswith(RESP_RELAY_MODE):
                self._parse_relay_mode(response.replace(RESP_RELAY_MODE, ""))
            
            # Humidification settings
            response = await self._send_command(CMD_GET_HUMIDIFICATION)
            if response and response.startswith(RESP_HUMIDIFICATION):
                self._parse_humidification(response.replace(RESP_HUMIDIFICATION, ""))
            
            # Dehumidification settings
            response = await self._send_command(CMD_GET_DEHUMIDIFICATION)
            if response and response.startswith(RESP_DEHUMIDIFICATION):
                self._parse_dehumidification(response.replace(RESP_DEHUMIDIFICATION, ""))
            
            # Relay state
            response = await self._send_command(CMD_GET_RELAY_STATE)
            if response and response.startswith(RESP_RELAY_STATE):
                self.state.relay_state = response.replace(RESP_RELAY_STATE, "").strip()
            
            # === HTTP SENSOR DATA ===
            await self._fetch_http_sensors()
            
            self.state.connected = True
            self.state.last_error = None
            
        except Exception as err:
            _LOGGER.error("Update error: %s", err)
            self.state.last_error = str(err)
            self.state.connected = False
        
        return self.state

    async def _get_http_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._http_session is None or self._http_session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._http_session = aiohttp.ClientSession(timeout=timeout)
        return self._http_session

    async def _fetch_http_sensors(self) -> None:
        """Fetch humidity and CO2 data via HTTP."""
        try:
            session = await self._get_http_session()
            
            # Fetch humidity from index.xml
            await self._fetch_humidity(session)
            
            # Fetch CO2 from co2.json
            await self._fetch_co2(session)
            
        except Exception as err:
            _LOGGER.debug("HTTP sensor fetch error (non-critical): %s", err)

    async def _fetch_humidity(self, session: aiohttp.ClientSession) -> None:
        """Fetch humidity from index.xml."""
        try:
            url = f"http://{self.host}/index.xml"
            async with session.get(url, auth=self._http_auth) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    # Parse humidity from XML: <humidity>25</humidity>
                    match = re.search(r'<humidity>(\d+)</humidity>', text, re.IGNORECASE)
                    if match:
                        self.state.humidity = int(match.group(1))
                        _LOGGER.debug("HTTP humidity: %s%%", self.state.humidity)
                else:
                    _LOGGER.debug("HTTP index.xml returned %s", response.status)
        except asyncio.TimeoutError:
            _LOGGER.debug("HTTP humidity fetch timeout")
        except Exception as err:
            _LOGGER.debug("HTTP humidity fetch error: %s", err)

    async def _fetch_co2(self, session: aiohttp.ClientSession) -> None:
        """Fetch CO2 data from co2.json."""
        try:
            url = f"http://{self.host}/co2.json"
            async with session.get(url, auth=self._http_auth) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        
                        # CO2 data is nested: {"co2": {"level": "635", ...}}
                        co2_data = data.get("co2", {})
                        
                        # Check if valid
                        if co2_data.get("valid", "").lower() != "true":
                            _LOGGER.debug("CO2 module reports invalid data")
                            return
                        
                        # Current CO2 level (comes as string)
                        level_str = co2_data.get("level", "")
                        if level_str:
                            try:
                                self.state.co2_level = int(level_str)
                                _LOGGER.debug("HTTP CO2 level: %s ppm", self.state.co2_level)
                            except ValueError:
                                pass
                        
                        # Peak CO2 level
                        peak_str = co2_data.get("peak_level", "")
                        if peak_str:
                            try:
                                self.state.co2_peak_level = int(peak_str)
                                _LOGGER.debug("HTTP CO2 peak: %s ppm", self.state.co2_peak_level)
                            except ValueError:
                                pass
                        
                        # Alert level
                        alert_str = co2_data.get("alert_level", "")
                        if alert_str:
                            try:
                                self.state.co2_alert_level = int(alert_str)
                            except ValueError:
                                pass
                        
                        # In alert state
                        self.state.co2_in_alert = co2_data.get("in_alert", "").lower() == "true"
                        
                    except Exception as json_err:
                        _LOGGER.debug("CO2 JSON parse error: %s", json_err)
                elif response.status == 404:
                    _LOGGER.debug("CO2 sensor not available (404)")
                else:
                    _LOGGER.debug("HTTP co2.json returned %s", response.status)
        except asyncio.TimeoutError:
            _LOGGER.debug("HTTP CO2 fetch timeout")
        except Exception as err:
            _LOGGER.debug("HTTP CO2 fetch error: %s", err)

    def _parse_all_states(self, data: str) -> None:
        """Parse RAS1 response."""
        try:
            parts = data.split(",")
            if len(parts) >= 11:
                self.state.indoor_temp = self._parse_temp(parts[0])
                self.state.outdoor_temp = self._parse_temp(parts[1])
                self.state.hvac_mode = parts[2].strip().upper()
                
                fan_str = parts[3].strip().upper()
                self.state.fan_mode = "ON" if "ON" in fan_str else "AUTO"
                
                self.state.override_active = parts[4].strip().upper() in ("YES", "Y", "TRUE", "1")
                self.state.recovery_active = parts[5].strip().upper() in ("YES", "Y", "TRUE", "1")
                
                try:
                    self.state.cool_setpoint = int(parts[6].strip())
                except (ValueError, TypeError):
                    pass
                
                try:
                    self.state.heat_setpoint = int(parts[7].strip())
                except (ValueError, TypeError):
                    pass
                
                self.state.operating_status = parts[8].strip().upper()
                
                try:
                    self.state.stage = int(parts[9].strip())
                    # Stage 0 = idle, Stage >= 1 = actively running
                    self.state.is_idle = (self.state.stage == 0)
                except (ValueError, TypeError):
                    self.state.stage = None
                    self.state.is_idle = True
                
                event = parts[10].strip()
                self.state.event = event if event.upper() != "NONE" else None
                
        except Exception as err:
            _LOGGER.error("Error parsing RAS1 '%s': %s", data, err)

    def _parse_temp(self, temp_str: str) -> float | None:
        """Parse temperature value."""
        temp_str = temp_str.strip().upper()
        if temp_str in ("NA", "--", "", "N/A"):
            return None
        try:
            return float(temp_str)
        except (ValueError, TypeError):
            return None

    def _parse_relay_mode(self, data: str) -> None:
        """Parse RMRF1 response."""
        try:
            parts = data.split(",")
            if len(parts) >= 2:
                self.state.relay1_mode = parts[0].strip().upper()
                self.state.relay2_mode = parts[1].strip().upper()
            elif len(parts) == 1:
                self.state.relay1_mode = parts[0].strip().upper()
        except Exception as err:
            _LOGGER.error("Error parsing RMRF1 '%s': %s", data, err)

    def _parse_humidification(self, data: str) -> None:
        """Parse RMHS1 response."""
        try:
            parts = data.split(",")
            if len(parts) >= 3:
                self.state.hum_control_mode = parts[0].strip().upper()
                self.state.hum_setpoint = int(parts[1].strip())
                self.state.hum_variance = int(parts[2].strip())
        except Exception as err:
            _LOGGER.error("Error parsing RMHS1 '%s': %s", data, err)

    def _parse_dehumidification(self, data: str) -> None:
        """Parse RMDHS1 response."""
        try:
            parts = data.split(",")
            if len(parts) >= 3:
                self.state.dehum_control_mode = parts[0].strip().upper()
                self.state.dehum_setpoint = int(parts[1].strip())
                self.state.dehum_variance = int(parts[2].strip())
        except Exception as err:
            _LOGGER.error("Error parsing RMDHS1 '%s': %s", data, err)

    def _validate_write_response(self, command: str, response: str | None, expected_value: str = None) -> bool:
        """Validate a write command response."""
        if response is None:
            return False
        if ":" not in response:
            _LOGGER.warning("Unexpected response format: %s", response)
            return False
        _LOGGER.debug("Write successful: %s -> %s", command, response)
        return True

    async def async_set_hvac_mode(self, mode: str) -> bool:
        """Set HVAC mode."""
        mode = mode.upper()
        if mode not in ("OFF", "HEAT", "COOL", "AUTO"):
            return False
        
        if self.state.is_manual_mode:
            command = f"{CMD_SET_MODE_MANUAL}{mode}"
        else:
            command = f"{CMD_SET_MODE_SCHEDULE}{mode}"
        
        response = await self._send_command(command)
        return self._validate_write_response(command, response)

    async def async_set_fan_mode(self, mode: str) -> bool:
        """Set fan mode."""
        mode = mode.upper()
        if mode not in ("AUTO", "ON"):
            return False
        
        if self.state.is_manual_mode:
            command = f"{CMD_SET_FAN_MANUAL}{mode}"
        else:
            command = f"{CMD_SET_FAN_SCHEDULE}{mode}"
        
        response = await self._send_command(command)
        return self._validate_write_response(command, response)

    async def async_set_cool_setpoint(self, temperature: int) -> bool:
        """Set cooling setpoint."""
        if self.state.is_manual_mode:
            command = f"{CMD_SET_COOL_MANUAL}{temperature}"
        else:
            command = f"{CMD_SET_COOL_SCHEDULE}{temperature}"
        
        response = await self._send_command(command)
        return self._validate_write_response(command, response)

    async def async_set_heat_setpoint(self, temperature: int) -> bool:
        """Set heating setpoint."""
        if self.state.is_manual_mode:
            command = f"{CMD_SET_HEAT_MANUAL}{temperature}"
        else:
            command = f"{CMD_SET_HEAT_SCHEDULE}{temperature}"
        
        response = await self._send_command(command)
        return self._validate_write_response(command, response)

    async def async_set_relay_mode(self, mode: str) -> bool:
        """Set humidity relay mode."""
        mode = mode.upper()
        if mode not in ("OFF", "HUM", "DEHUM"):
            return False
        
        command = f"{CMD_SET_RELAY_MODE}{mode}"
        response = await self._send_command(command)
        return self._validate_write_response(command, response)

    async def async_set_humidification(self, independent: bool, setpoint: int, variance: int = 5) -> bool:
        """Set humidification settings."""
        mode = "IH" if independent else "WH"
        setpoint = max(10, min(90, setpoint))
        variance = max(2, min(10, variance))
        
        command = f"{CMD_SET_HUMIDIFICATION}{mode},{setpoint},{variance}"
        response = await self._send_command(command)
        return self._validate_write_response(command, response)

    async def async_set_dehumidification(self, independent: bool, setpoint: int, variance: int = 5) -> bool:
        """Set dehumidification settings."""
        mode = "IC" if independent else "WC"
        setpoint = max(10, min(90, setpoint))
        variance = max(2, min(10, variance))
        
        command = f"{CMD_SET_DEHUMIDIFICATION}{mode},{setpoint},{variance}"
        response = await self._send_command(command)
        return self._validate_write_response(command, response)

    async def test_connection(self) -> bool:
        """Test connection to the thermostat."""
        if await self.connect():
            response = await self._send_command(CMD_GET_TEMP_SCALE)
            return response is not None
        return False
