"""Data coordinator for NetX Thermostat integration."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL
from .api import NetXThermostatAPI, NetXThermostatState

_LOGGER = logging.getLogger(__name__)


class NetXDataUpdateCoordinator(DataUpdateCoordinator[NetXThermostatState]):
    """Class to manage fetching NetX data."""

    def __init__(self, hass: HomeAssistant, api: NetXThermostatAPI) -> None:
        """Initialize the coordinator."""
        self.api = api

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> NetXThermostatState:
        """Fetch data from TCP API."""
        try:
            state = await self.api.async_update()
            
            if not state.connected:
                raise UpdateFailed(f"Failed to connect: {state.last_error}")
            
            return state

        except Exception as err:
            raise UpdateFailed(f"Error communicating with thermostat: {err}")

    async def async_shutdown(self) -> None:
        """Disconnect on shutdown."""
        await self.api.disconnect()
