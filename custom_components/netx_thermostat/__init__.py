# __init__.py
import asyncio
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EcoFlow DELTA 2 Max from a config entry."""
    hass.data.setdefault("ecoflow_delta2max", {})

    coordinator = EcoFlowDelta2MaxCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data["ecoflow_delta2max"][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data["ecoflow_delta2max"].pop(entry.entry_id)
    return unload_ok
