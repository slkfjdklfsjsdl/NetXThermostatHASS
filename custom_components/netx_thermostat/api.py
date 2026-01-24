"""NetX Thermostat Client."""
import asyncio
import hashlib
import base64
import logging
from dataclasses import dataclass
from typing import Any

from .const import (
    DEFAULT_PORT,
    CONNECTION_TIMEOUT,
    COMMAND_TIMEOUT,
    CMD_LOGIN,
    CMD_GET_TEMP_SCALE,
    CMD_GET_ALL_STATES,
    CMD_GET_HUMIDITY,
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
    CMD_SET_TEMP_SCALE,
    CMD_SET_RELAY_MODE,
    CMD_SET_HUMIDIFICATION,
    CMD_SET_DEHUMIDIFICATION,
    RESP_LOGIN_OK,
    RESP_TEMP_SCALE,
    RESP_ALL_STATES,
    RESP_HUMIDITY,
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
    hvac_mode: str | None = None  # OFF, HEAT, COOL, AUTO
    fan_mode: str | None = None  # AUTO, ON
    override_active: bool = False
    recovery_active: bool = False
    cool_setpoint: int | None = None
    heat_setpoint: int | None = None
    operating_status: str | None = None  # What's actually running
    stage: int | None = None
    event: str | None = None
    
    # From other commands
    humidity: int | None = None  # From RRHS1
    temp_scale: str = "F"  # From RTS1
    is_manual_mode: bool = True  # From RNS1
    operation_mode: str = "Manual"  # Human readable
    
    # Humidity control from RMRF1, RMHS1, RMDHS1
    relay1_mode: str | None = None  # OFF, HUM, DEHUM
    relay2_mode: str | None = None  # OFF, HUM, DEHUM
    relay_state: str | None = None  # From RRS1
    
    # Humidification settings (from RMHS1: WH,50,5)
    hum_control_mode: str | None = None  # WH (With Heating) or IH (Independent of Heating)
    hum_setpoint: int | None = None  # Target humidity %
    hum_variance: int | None = None  # +/- variance %
    
    # Dehumidification settings (from RMDHS1: IC,55,5)
    dehum_control_mode: str | None = None  # WC (With Cooling) or IC (Independent of Cooling)
    dehum_setpoint: int | None = None  # Target humidity %
    dehum_variance: int | None = None  # +/- variance %
    
    # Connection status
    connected: bool = False
    last_error: str | None = None


class NetXThermostatAPI:
    """TCP API client for NetX Thermostat."""

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
        
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._authenticated = False
        
        self.state = NetXThermostatState()

    def _generate_auth_hash(self) -> str:
        """Generate the authentication hash (SHA256 of username:password, base64 encoded)."""
        auth_string = f"{self.username}:{self.password}"
        sha256_hash = hashlib.sha256(auth_string.encode()).digest()
        return base64.b64encode(sha256_hash).decode()

    async def connect(self) -> bool:
        """Connect and authenticate with the thermostat."""
        try:
            async with self._lock:
                # Close existing connection if any
                await self._close_connection_locked()
                
                # Open new connection
                _LOGGER.debug("Connecting to %s:%s", self.host, self.port)
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=CONNECTION_TIMEOUT
                )
                
                # Authenticate
                auth_hash = self._generate_auth_hash()
                login_cmd = f"{CMD_LOGIN}{self.username},{auth_hash}\r\n"
                
                _LOGGER.debug("Sending login command")
                self._writer.write(login_cmd.encode())
                await self._writer.drain()
                
                response = await asyncio.wait_for(
                    self._reader.readline(),
                    timeout=COMMAND_TIMEOUT
                )
                response_str = response.decode().strip()
                
                _LOGGER.debug("Login response: %s", response_str)
                
                if response_str.startswith(RESP_LOGIN_OK):
                    self._authenticated = True
                    self.state.connected = True
                    self.state.last_error = None
                    _LOGGER.info("Successfully connected to NetX Thermostat at %s", self.host)
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
            _LOGGER.error("Connection error to %s:%s - %s", self.host, self.port, err)
            return False
        except Exception as err:
            self.state.connected = False
            self.state.last_error = str(err)
            _LOGGER.error("Unexpected connection error: %s", err)
            return False

    async def _close_connection_locked(self) -> None:
        """Close the connection (must be called with lock held)."""
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
            _LOGGER.debug("Disconnected from thermostat")

    async def _send_command(self, command: str) -> str | None:
        """Send a command and receive response."""
        # Reconnect if needed
        if not self._authenticated:
            if not await self.connect():
                return None
        
        try:
            async with self._lock:
                if not self._writer or not self._reader:
                    _LOGGER.warning("No connection available for command: %s", command)
                    return None
                
                # Send command
                full_command = f"{command}\r\n"
                self._writer.write(full_command.encode())
                await self._writer.drain()
                
                # Receive response
                response = await asyncio.wait_for(
                    self._reader.readline(),
                    timeout=COMMAND_TIMEOUT
                )
                response_str = response.decode().strip()
                
                _LOGGER.debug("Command: %s -> Response: %s", command, response_str)
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
            # Get temperature scale
            response = await self._send_command(CMD_GET_TEMP_SCALE)
            if response and response.startswith(RESP_TEMP_SCALE):
                scale = response.replace(RESP_TEMP_SCALE, "").strip()
                self.state.temp_scale = "F" if "FAHRENHEIT" in scale.upper() else "C"
            
            # Get all states (main data) - this is the important one
            response = await self._send_command(CMD_GET_ALL_STATES)
            if response and response.startswith(RESP_ALL_STATES):
                self._parse_all_states(response.replace(RESP_ALL_STATES, ""))
            
            # Get humidity
            response = await self._send_command(CMD_GET_HUMIDITY)
            if response and response.startswith(RESP_HUMIDITY):
                try:
                    humidity_str = response.replace(RESP_HUMIDITY, "").strip()
                    self.state.humidity = int(humidity_str) if humidity_str.isdigit() else None
                except (ValueError, TypeError):
                    self.state.humidity = None
            
            # Get operation mode (manual vs schedule)
            response = await self._send_command(CMD_GET_OPERATION_MODE)
            if response and response.startswith(RESP_OPERATION_MODE):
                mode = response.replace(RESP_OPERATION_MODE, "").strip()
                self.state.is_manual_mode = (mode == OPERATION_MODE_MANUAL)
                self.state.operation_mode = "Manual" if self.state.is_manual_mode else "Schedule"
            
            # Get humidity relay mode (RMRF1:OFF,OFF)
            response = await self._send_command(CMD_GET_RELAY_MODE)
            if response and response.startswith(RESP_RELAY_MODE):
                self._parse_relay_mode(response.replace(RESP_RELAY_MODE, ""))
            
            # Get humidification settings (RMHS1:WH,50,5)
            response = await self._send_command(CMD_GET_HUMIDIFICATION)
            if response and response.startswith(RESP_HUMIDIFICATION):
                self._parse_humidification(response.replace(RESP_HUMIDIFICATION, ""))
            
            # Get dehumidification settings (RMDHS1:IC,55,5)
            response = await self._send_command(CMD_GET_DEHUMIDIFICATION)
            if response and response.startswith(RESP_DEHUMIDIFICATION):
                self._parse_dehumidification(response.replace(RESP_DEHUMIDIFICATION, ""))
            
            # Get relay state (RRS1:OFF)
            response = await self._send_command(CMD_GET_RELAY_STATE)
            if response and response.startswith(RESP_RELAY_STATE):
                self.state.relay_state = response.replace(RESP_RELAY_STATE, "").strip()
            
            self.state.connected = True
            self.state.last_error = None
            
        except Exception as err:
            _LOGGER.error("Update error: %s", err)
            self.state.last_error = str(err)
            self.state.connected = False
        
        return self.state

    def _parse_relay_mode(self, data: str) -> None:
        """
        Parse RMRF1 response.
        
        Format: {relay1_mode},{relay2_mode}
        Example: OFF,OFF or HUM,OFF or DEHUM,OFF
        """
        try:
            parts = data.split(",")
            if len(parts) >= 2:
                self.state.relay1_mode = parts[0].strip().upper()
                self.state.relay2_mode = parts[1].strip().upper()
            elif len(parts) == 1:
                self.state.relay1_mode = parts[0].strip().upper()
        except Exception as err:
            _LOGGER.error("Error parsing RMRF1 response '%s': %s", data, err)

    def _parse_humidification(self, data: str) -> None:
        """
        Parse RMHS1 response.
        
        Format: {mode},{setpoint},{variance}
        Example: WH,50,5 means With Heating, 50% setpoint, ±5% variance
        """
        try:
            parts = data.split(",")
            if len(parts) >= 3:
                self.state.hum_control_mode = parts[0].strip().upper()
                self.state.hum_setpoint = int(parts[1].strip())
                self.state.hum_variance = int(parts[2].strip())
            _LOGGER.debug("Parsed humidification: mode=%s, setpoint=%s, variance=%s",
                         self.state.hum_control_mode, self.state.hum_setpoint, self.state.hum_variance)
        except Exception as err:
            _LOGGER.error("Error parsing RMHS1 response '%s': %s", data, err)

    def _parse_dehumidification(self, data: str) -> None:
        """
        Parse RMDHS1 response.
        
        Format: {mode},{setpoint},{variance}
        Example: IC,55,5 means Independent of Cooling, 55% setpoint, ±5% variance
        """
        try:
            parts = data.split(",")
            if len(parts) >= 3:
                self.state.dehum_control_mode = parts[0].strip().upper()
                self.state.dehum_setpoint = int(parts[1].strip())
                self.state.dehum_variance = int(parts[2].strip())
            _LOGGER.debug("Parsed dehumidification: mode=%s, setpoint=%s, variance=%s",
                         self.state.dehum_control_mode, self.state.dehum_setpoint, self.state.dehum_variance)
        except Exception as err:
            _LOGGER.error("Error parsing RMDHS1 response '%s': %s", data, err)

    def _parse_all_states(self, data: str) -> None:
        """
        Parse RAS1 response.
        
        Format: indoor,outdoor,mode,fan,override,recovery,spcool,spheat,opstatus,stage,event
        Example: 68,NA,HEAT,FAN ON,NO,NO,77,68,HEAT,1,NONE
        """
        try:
            parts = data.split(",")
            _LOGGER.debug("Parsing RAS1 with %d parts: %s", len(parts), parts)
            
            if len(parts) >= 11:
                # Indoor temperature
                self.state.indoor_temp = self._parse_temp(parts[0])
                
                # Outdoor temperature
                self.state.outdoor_temp = self._parse_temp(parts[1])
                
                # HVAC mode (OFF, HEAT, COOL, AUTO)
                self.state.hvac_mode = parts[2].strip().upper()
                
                # Fan mode - handle "FAN ON" vs "FAN AUTO" vs just "ON"/"AUTO"
                fan_str = parts[3].strip().upper()
                if "ON" in fan_str:
                    self.state.fan_mode = "ON"
                else:
                    self.state.fan_mode = "AUTO"
                
                # Override active
                self.state.override_active = parts[4].strip().upper() in ("YES", "Y", "TRUE", "1")
                
                # Recovery active
                self.state.recovery_active = parts[5].strip().upper() in ("YES", "Y", "TRUE", "1")
                
                # Cool setpoint
                try:
                    self.state.cool_setpoint = int(parts[6].strip())
                except (ValueError, TypeError):
                    pass
                
                # Heat setpoint
                try:
                    self.state.heat_setpoint = int(parts[7].strip())
                except (ValueError, TypeError):
                    pass
                
                # Operating status (what's actually running: HEAT, COOL, OFF, etc.)
                self.state.operating_status = parts[8].strip().upper()
                
                # Stage
                try:
                    self.state.stage = int(parts[9].strip())
                except (ValueError, TypeError):
                    self.state.stage = None
                
                # Event
                event = parts[10].strip()
                self.state.event = event if event.upper() != "NONE" else None
            else:
                _LOGGER.warning("RAS1 response has fewer than 11 parts: %s", data)
                
        except Exception as err:
            _LOGGER.error("Error parsing RAS1 response '%s': %s", data, err)

    def _parse_temp(self, temp_str: str) -> float | None:
        """Parse temperature value, handling NA and other invalid values."""
        temp_str = temp_str.strip().upper()
        if temp_str in ("NA", "--", "", "N/A"):
            return None
        try:
            return float(temp_str)
        except (ValueError, TypeError):
            return None

    # ----- Write Commands -----

    def _validate_write_response(self, command: str, response: str | None, expected_value: str = None) -> bool:
        """
        Validate a write command response.
        
        Response format: {COMMAND}:{VALUE_SET}
        Example: WNHD1D70:70 means command accepted, value set to 70
        """
        if response is None:
            return False
        
        # Response should contain the command and a colon
        if ":" not in response:
            _LOGGER.warning("Unexpected response format: %s", response)
            return False
        
        # Parse response
        parts = response.split(":", 1)
        if len(parts) != 2:
            return False
        
        resp_command, resp_value = parts
        
        # Verify the response matches our command
        if not response.startswith(command.split("D")[0]):  # Match command prefix
            _LOGGER.warning("Response command mismatch: sent %s, got %s", command, resp_command)
            return False
        
        # If we expected a specific value, verify it
        if expected_value is not None and resp_value.strip() != str(expected_value):
            _LOGGER.warning("Response value mismatch: expected %s, got %s", expected_value, resp_value)
            return False
        
        _LOGGER.debug("Write command successful: %s -> %s", command, response)
        return True

    async def async_set_hvac_mode(self, mode: str) -> bool:
        """Set HVAC mode (OFF, HEAT, COOL, AUTO)."""
        mode = mode.upper()
        if mode not in ("OFF", "HEAT", "COOL", "AUTO"):
            _LOGGER.error("Invalid HVAC mode: %s", mode)
            return False
        
        # Use the correct command based on current operation mode
        if self.state.is_manual_mode:
            command = f"{CMD_SET_MODE_MANUAL}{mode}"
        else:
            command = f"{CMD_SET_MODE_SCHEDULE}{mode}"
        
        _LOGGER.debug("Setting HVAC mode to %s (manual=%s)", mode, self.state.is_manual_mode)
        response = await self._send_command(command)
        return self._validate_write_response(command, response, mode)

    async def async_set_fan_mode(self, mode: str) -> bool:
        """Set fan mode (AUTO, ON)."""
        mode = mode.upper()
        if mode not in ("AUTO", "ON"):
            _LOGGER.error("Invalid fan mode: %s", mode)
            return False
        
        if self.state.is_manual_mode:
            command = f"{CMD_SET_FAN_MANUAL}{mode}"
        else:
            command = f"{CMD_SET_FAN_SCHEDULE}{mode}"
        
        _LOGGER.debug("Setting fan mode to %s", mode)
        response = await self._send_command(command)
        return self._validate_write_response(command, response, mode)

    async def async_set_cool_setpoint(self, temperature: int) -> bool:
        """Set cooling setpoint."""
        if self.state.is_manual_mode:
            command = f"{CMD_SET_COOL_MANUAL}{temperature}"
        else:
            command = f"{CMD_SET_COOL_SCHEDULE}{temperature}"
        
        _LOGGER.debug("Setting cool setpoint to %s", temperature)
        response = await self._send_command(command)
        return self._validate_write_response(command, response, str(temperature))

    async def async_set_heat_setpoint(self, temperature: int) -> bool:
        """Set heating setpoint."""
        if self.state.is_manual_mode:
            command = f"{CMD_SET_HEAT_MANUAL}{temperature}"
        else:
            command = f"{CMD_SET_HEAT_SCHEDULE}{temperature}"
        
        _LOGGER.debug("Setting heat setpoint to %s", temperature)
        response = await self._send_command(command)
        return self._validate_write_response(command, response, str(temperature))

    async def async_set_temperature_scale(self, scale: str) -> bool:
        """Set temperature scale (F or C)."""
        scale = scale.upper()[0]  # Just F or C
        if scale not in ("F", "C"):
            _LOGGER.error("Invalid temperature scale: %s", scale)
            return False
        
        command = f"{CMD_SET_TEMP_SCALE}{scale}"
        _LOGGER.debug("Setting temperature scale to %s", scale)
        response = await self._send_command(command)
        return self._validate_write_response(command, response, scale)

    async def async_set_relay_mode(self, mode: str) -> bool:
        """Set humidity relay mode (OFF, HUM, DEHUM)."""
        mode = mode.upper()
        if mode not in ("OFF", "HUM", "DEHUM"):
            _LOGGER.error("Invalid relay mode: %s", mode)
            return False
        
        command = f"{CMD_SET_RELAY_MODE}{mode}"
        _LOGGER.debug("Setting relay mode to %s", mode)
        response = await self._send_command(command)
        return self._validate_write_response(command, response)

    async def async_set_humidification(
        self, 
        independent: bool, 
        setpoint: int, 
        variance: int = 5
    ) -> bool:
        """
        Set humidification settings.
        
        Args:
            independent: If True, run independently of heating. If False, run with heating.
            setpoint: Target humidity percentage (10-90)
            variance: +/- variance percentage (2-10)
        """
        mode = "IH" if independent else "WH"  # IH = Independent of Heating, WH = With Heating
        
        # Clamp values to valid range
        setpoint = max(10, min(90, setpoint))
        variance = max(2, min(10, variance))
        
        command = f"{CMD_SET_HUMIDIFICATION}{mode},{setpoint},{variance}"
        _LOGGER.debug("Setting humidification: mode=%s, setpoint=%s, variance=%s", mode, setpoint, variance)
        response = await self._send_command(command)
        return self._validate_write_response(command, response)

    async def async_set_dehumidification(
        self, 
        independent: bool, 
        setpoint: int, 
        variance: int = 5
    ) -> bool:
        """
        Set dehumidification settings.
        
        Args:
            independent: If True, run independently of cooling. If False, run with cooling.
            setpoint: Target humidity percentage (10-90)
            variance: +/- variance percentage (2-10)
        """
        mode = "IC" if independent else "WC"  # IC = Independent of Cooling, WC = With Cooling
        
        # Clamp values to valid range
        setpoint = max(10, min(90, setpoint))
        variance = max(2, min(10, variance))
        
        command = f"{CMD_SET_DEHUMIDIFICATION}{mode},{setpoint},{variance}"
        _LOGGER.debug("Setting dehumidification: mode=%s, setpoint=%s, variance=%s", mode, setpoint, variance)
        response = await self._send_command(command)
        return self._validate_write_response(command, response)

    async def test_connection(self) -> bool:
        """Test connection to the thermostat."""
        if await self.connect():
            # Try to get state to verify full connectivity
            response = await self._send_command(CMD_GET_TEMP_SCALE)
            return response is not None
        return False
