"""Button platform for NetX Thermostat integration."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, ENDPOINT_REBOOT
from .coordinator import NetXDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the NetX Thermostat button platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]

    buttons = [
        NetXRebootButton(coordinator, config_entry),
    ]

    async_add_entities(buttons)


class NetXRebootButton(ButtonEntity):
    """Representation of a NetX Thermostat Reboot Button."""

    _attr_has_entity_name = True
    _attr_name = "Restart"
    _attr_icon = "mdi:restart"

    def __init__(
        self,
        coordinator: NetXDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{config_entry.entry_id}_restart"
        
        device_name = config_entry.data.get("device_name", "NetX Thermostat")
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": device_name,
            "manufacturer": "NetX",
            "model": "Thermostat",
        }

    async def async_press(self) -> None:
        """Handle the button press - restart the thermostat."""
        # Use GET request for reboot endpoint
        try:
            session = await self._coordinator._get_session()
            url = f"http://{self._coordinator.host}{ENDPOINT_REBOOT}"
            
            async with session.get(
                url, auth=self._coordinator.auth
            ) as response:
                if response.status == 200:
                    _LOGGER.info("Thermostat restart command sent successfully")
                else:
                    _LOGGER.error(
                        "Failed to restart thermostat: %s", response.status
                    )
        except Exception as err:
            _LOGGER.error("Error sending restart command: %s", err)
