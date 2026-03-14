import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD


class VR7ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VR7."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        if user_input is not None:
            return self.async_create_entry(
                title="Vorwerk VR7",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )