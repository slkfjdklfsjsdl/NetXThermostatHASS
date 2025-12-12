"""Config flow for NetX Thermostat integration."""
import logging
import voluptuous as vol
import aiohttp
import xml.etree.ElementTree as ET

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.1.2"): str,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict):
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]

    url = f"http://{host}/index.xml"
    auth = aiohttp.BasicAuth(username, password)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=auth, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 401:
                    raise InvalidAuth
                if response.status != 200:
                    raise CannotConnect
                
                text = await response.text()
                root = ET.fromstring(text)
                isvalid = root.find("isvalid")
                
                if isvalid is None or isvalid.text != "1":
                    raise InvalidAuth
                    
    except aiohttp.ClientError:
        raise CannotConnect
    except ET.ParseError:
        raise CannotConnect

    return {"title": f"NetX Thermostat ({host})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NetX Thermostat."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
