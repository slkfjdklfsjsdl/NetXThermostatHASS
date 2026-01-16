"""The NetX Thermostat integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import NetXDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate", "sensor", "button", "switch", "select", "number"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NetX Thermostat from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create shared coordinator
    coordinator = NetXDataUpdateCoordinator(
        hass,
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and config data
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config": entry.data,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Close the coordinator session
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["coordinator"].close()
    return unload_ok
