"""Config flow for NetX Thermostat integration."""
import logging
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, ENDPOINT_INDEX_XML

_LOGGER = logging.getLogger(__name__)


async def validate_connection(
    hass: HomeAssistant, 
    host: str, 
    username: str, 
    password: str
) -> bool:
    """Validate the user input allows us to connect."""
    try:
        auth = aiohttp.BasicAuth(username, password)
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"http://{host}{ENDPOINT_INDEX_XML}"
            async with session.get(url, auth=auth) as response:
                return response.status == 200
    except Exception as err:
        _LOGGER.error("Error connecting to thermostat: %s", err)
        return False


class NetXThermostatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NetX Thermostat."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate connection
            valid = await validate_connection(
                self.hass,
                user_input[CONF_HOST],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            if valid:
                # Create unique ID from host
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input.get("device_name", "NetX Thermostat"),
                    data=user_input,
                )
            else:
                errors["base"] = "cannot_connect"

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional("device_name", default="NetX Thermostat"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
