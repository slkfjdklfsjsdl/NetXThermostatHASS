"""The NetX Thermostat integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, DEFAULT_PORT
from .api import NetXThermostatAPI
from .coordinator import NetXTCPDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.SWITCH, Platform.NUMBER, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NetX Thermostat from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create API client
    api = NetXThermostatAPI(
        host=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
    )
    
    # Test connection
    if not await api.test_connection():
        raise ConfigEntryNotReady(
            f"Failed to connect to NetX Thermostat at {entry.data[CONF_HOST]}: {api.state.last_error}"
        )
    
    # Create coordinator
    coordinator = NetXTCPDataUpdateCoordinator(hass, api)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        # Disconnect from thermostat
        await data["api"].disconnect()
    return unload_ok
