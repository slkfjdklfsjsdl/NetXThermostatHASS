"""Data coordinator for NetX Thermostat integration."""
import logging
import re
from datetime import timedelta
import aiohttp
import xml.etree.ElementTree as ET
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    UPDATE_INTERVAL,
    ENDPOINT_INDEX_XML,
    ENDPOINT_CO2_JSON,
    ENDPOINT_CONFIG_HUMIDITY,
    ENDPOINT_SCHEDULE_XML,
)

_LOGGER = logging.getLogger(__name__)


class NetXDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching NetX data."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        host: str, 
        username: str, 
        password: str
    ) -> None:
        """Initialize."""
        self.host = host
        self.username = username
        self.password = password
        self.auth = aiohttp.BasicAuth(username, password)
        self._session: aiohttp.ClientSession | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        try:
            session = await self._get_session()
            data = {}
            
            # Fetch index.xml
            xml_url = f"http://{self.host}{ENDPOINT_INDEX_XML}"
            async with session.get(xml_url, auth=self.auth) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error fetching data: {response.status}")
                xml_text = await response.text()

            # Parse XML
            root = ET.fromstring(xml_text)
            for child in root:
                data[child.tag] = child.text

            # Fetch co2.json
            co2_url = f"http://{self.host}{ENDPOINT_CO2_JSON}"
            try:
                async with session.get(co2_url, auth=self.auth) as response:
                    if response.status == 200:
                        co2_data = await response.json()
                        if co2_data and "co2" in co2_data:
                            co2_info = co2_data["co2"]
                            data["co2_level"] = co2_info.get("level")
                            data["co2_peak_level"] = co2_info.get("peak_level")
                            data["co2_alert_level"] = co2_info.get("alert_level")
                            data["co2_type"] = co2_info.get("type")
                            data["co2_valid"] = co2_info.get("valid")
                            data["co2_in_alert"] = co2_info.get("in_alert")
                            data["co2_peak_reset"] = co2_info.get("peak_reset")
                            data["co2_display"] = co2_info.get("display")
                            data["co2_relay_high"] = co2_info.get("relay_high")
                            data["co2_relay_failure"] = co2_info.get("relay_failure")
            except (aiohttp.ClientError, ValueError):
                # CO2 endpoint may not exist on all models
                pass

            # Fetch humidity configuration from HTML page
            try:
                humidity_url = f"http://{self.host}{ENDPOINT_CONFIG_HUMIDITY}"
                async with session.get(humidity_url, auth=self.auth) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        # Parse humidity settings from HTML
                        humidity_config = self._parse_humidity_config(html_content)
                        data.update(humidity_config)
            except (aiohttp.ClientError, ValueError) as err:
                _LOGGER.debug("Could not fetch humidity config: %s", err)

            # Fetch schedule data
            try:
                schedule_url = f"http://{self.host}{ENDPOINT_SCHEDULE_XML}"
                async with session.get(schedule_url, auth=self.auth) as response:
                    if response.status == 200:
                        schedule_xml = await response.text()
                        schedule_data = self._parse_schedule_xml(schedule_xml)
                        data["schedule"] = schedule_data
            except (aiohttp.ClientError, ValueError, ET.ParseError) as err:
                _LOGGER.debug("Could not fetch schedule: %s", err)

            return data

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with device: {err}")
        except ET.ParseError as err:
            raise UpdateFailed(f"Error parsing XML: {err}")

    def _parse_humidity_config(self, html_content: str) -> dict[str, Any]:
        """Parse humidity configuration from HTML page."""
        config = {}
        
        # Parse relay mode from JavaScript: let relVal1 = "3";
        rel_match = re.search(r'let\s+relVal1\s*=\s*["\'](\d+)["\']', html_content)
        if rel_match:
            config["humidity_relay_mode"] = int(rel_match.group(1))
        
        # Parse dehumidification settings from JavaScript updateSelect calls
        # updateSelect("DropDownDehum", "1") means Independent of Cooling
        dehum_mode_match = re.search(
            r'updateSelect\s*\(\s*["\']DropDownDehum["\']\s*,\s*["\'](\d+)["\']\s*\)', 
            html_content
        )
        if dehum_mode_match:
            config["dehum_independent"] = int(dehum_mode_match.group(1))
        
        # Parse humidification settings from JavaScript
        # updateSelect("DropDownHum", "0") means With Heating Only
        hum_mode_match = re.search(
            r'updateSelect\s*\(\s*["\']DropDownHum["\']\s*,\s*["\'](\d+)["\']\s*\)', 
            html_content
        )
        if hum_mode_match:
            config["hum_independent"] = int(hum_mode_match.group(1))
        
        # Parse dehumidification setpoint from input field
        # <input id="spdehum" name="spdehum" type="text" class="intext" value="55"/>
        spdehum_match = re.search(
            r'id=["\']spdehum["\'][^>]*value=["\'](\d+)["\']', 
            html_content
        )
        if not spdehum_match:
            spdehum_match = re.search(
                r'name=["\']spdehum["\'][^>]*value=["\'](\d+)["\']', 
                html_content
            )
        if spdehum_match:
            config["dehum_setpoint"] = int(spdehum_match.group(1))
        
        # Parse dehumidification variance
        spvdehum_match = re.search(
            r'id=["\']spvdehum["\'][^>]*value=["\'](\d+)["\']', 
            html_content
        )
        if not spvdehum_match:
            spvdehum_match = re.search(
                r'name=["\']spvdehum["\'][^>]*value=["\'](\d+)["\']', 
                html_content
            )
        if spvdehum_match:
            config["dehum_variance"] = int(spvdehum_match.group(1))
        
        # Parse humidification setpoint
        sphum_match = re.search(
            r'id=["\']sphum["\'][^>]*value=["\'](\d+)["\']', 
            html_content
        )
        if not sphum_match:
            sphum_match = re.search(
                r'name=["\']sphum["\'][^>]*value=["\'](\d+)["\']', 
                html_content
            )
        if sphum_match:
            config["hum_setpoint"] = int(sphum_match.group(1))
        
        # Parse humidification variance
        spvhum_match = re.search(
            r'id=["\']spvhum["\'][^>]*value=["\'](\d+)["\']', 
            html_content
        )
        if not spvhum_match:
            spvhum_match = re.search(
                r'name=["\']spvhum["\'][^>]*value=["\'](\d+)["\']', 
                html_content
            )
        if spvhum_match:
            config["hum_variance"] = int(spvhum_match.group(1))
        
        # Parse damper control setting
        damper_match = re.search(
            r'updateSelect\s*\(\s*["\']DropDownDamper["\']\s*,\s*["\'](\d+)["\']\s*\)', 
            html_content
        )
        if damper_match:
            config["damper_control"] = int(damper_match.group(1))
        
        # Parse aux relay setting
        aux_match = re.search(
            r'updateSelect\s*\(\s*["\']DropDownAux["\']\s*,\s*["\'](\d+)["\']\s*\)', 
            html_content
        )
        if aux_match:
            config["aux_relay"] = int(aux_match.group(1))
        
        return config

    def _parse_schedule_xml(self, xml_content: str) -> dict[str, Any]:
        """Parse schedule XML data."""
        schedule = {}
        try:
            root = ET.fromstring(xml_content)
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            
            for day in days:
                day_elem = root.find(day)
                if day_elem is not None:
                    day_schedules = []
                    for i in range(1, 5):  # Up to 4 schedules per day
                        sch_elem = day_elem.find(f'sch{i}')
                        if sch_elem is not None:
                            sch_data = {
                                'active': sch_elem.findtext('a', 'I') == 'A',  # A=Active, I=Inactive
                                'time': sch_elem.findtext('t', ''),
                                'cool_setpoint': sch_elem.findtext('c', ''),
                                'heat_setpoint': sch_elem.findtext('h', ''),
                                'occupancy': 'Occupied' if sch_elem.findtext('o', 'O') == 'O' else 'Unoccupied',
                                'mode': self._decode_mode(sch_elem.findtext('m', 'A')),
                                'fan': 'Auto' if sch_elem.findtext('f', 'A') == 'A' else 'On',
                            }
                            day_schedules.append(sch_data)
                    schedule[day] = day_schedules
        except ET.ParseError as err:
            _LOGGER.debug("Error parsing schedule XML: %s", err)
        
        return schedule

    def _decode_mode(self, mode_code: str) -> str:
        """Decode mode code to human readable."""
        modes = {
            'A': 'Auto',
            'H': 'Heat',
            'C': 'Cool',
            'O': 'Off',
        }
        return modes.get(mode_code.upper(), mode_code)

    async def async_send_command(
        self, 
        endpoint: str, 
        data: dict[str, Any]
    ) -> bool:
        """Send a command to the thermostat."""
        try:
            session = await self._get_session()
            url = f"http://{self.host}{endpoint}"
            
            async with session.post(url, data=data, auth=self.auth) as response:
                if response.status == 200:
                    return True
                else:
                    _LOGGER.error(
                        "Failed to send command to %s: %s", 
                        endpoint, 
                        response.status
                    )
                    return False
        except aiohttp.ClientError as err:
            _LOGGER.error("Error sending command: %s", err)
            return False
