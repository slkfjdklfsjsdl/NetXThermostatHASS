"""Config flow for NetX Thermostat integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, DEFAULT_PORT
from .api import NetXThermostatAPI

_LOGGER = logging.getLogger(__name__)


class NetXThermostatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NetX Thermostat."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            api = NetXThermostatAPI(
                host=user_input[CONF_HOST],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                port=user_input.get(CONF_PORT, DEFAULT_PORT),
            )
            
            try:
                if await api.test_connection():
                    await self.async_set_unique_id(user_input[CONF_HOST])
                    self._abort_if_unique_id_configured()
                    await api.disconnect()

                    return self.async_create_entry(
                        title=user_input.get("device_name", f"NetX Thermostat ({user_input[CONF_HOST]})"),
                        data=user_input,
                    )
                else:
                    errors["base"] = "cannot_connect"
                    _LOGGER.error("Connection failed: %s", api.state.last_error)
            except Exception as err:
                errors["base"] = "cannot_connect"
                _LOGGER.error("Connection error: %s", err)
            finally:
                await api.disconnect()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_USERNAME, default="admin"): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional("device_name", default="NetX Thermostat"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
