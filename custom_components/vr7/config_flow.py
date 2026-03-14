import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_EMAIL, CONF_OTP, CONF_TOKEN, AUTH_HOST

_LOGGER = logging.getLogger(__name__)


class VR7ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle VR7 config flow."""

    VERSION = 1
    email = None

    async def async_step_user(self, user_input=None):
        """Step 1: ask for email."""

        errors = {}

        if user_input is not None:
            self.email = user_input[CONF_EMAIL]

            try:
                session = async_get_clientsession(self.hass)

                await session.post(
                    f"{AUTH_HOST}/passwordless/start",
                    json={
                        "connection": "email",
                        "email": self.email,
                        "send": "code",
                    },
                )

                return await self.async_step_otp()

            except Exception as err:
                _LOGGER.error("OTP send failed: %s", err)
                errors["base"] = "cannot_send_otp"

        schema = vol.Schema({
            vol.Required(CONF_EMAIL): str
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_otp(self, user_input=None):
        """Step 2: validate OTP."""

        errors = {}

        if user_input is not None:

            try:
                session = async_get_clientsession(self.hass)

                response = await session.post(
                    f"{AUTH_HOST}/oauth/token",
                    json={
                        "grant_type": "http://auth0.com/oauth/grant-type/passwordless/otp",
                        "username": self.email,
                        "otp": user_input[CONF_OTP],
                        "realm": "email",
                        "scope": "openid profile email",
                    },
                )

                data = await response.json()

                token = data["access_token"]

                return self.async_create_entry(
                    title="Vorwerk VR7",
                    data={
                        CONF_EMAIL: self.email,
                        CONF_TOKEN: token,
                    },
                )

            except Exception as err:
                _LOGGER.error("OTP validation failed: %s", err)
                errors["base"] = "invalid_otp"

        schema = vol.Schema({
            vol.Required(CONF_OTP): str
        })

        return self.async_show_form(
            step_id="otp",
            data_schema=schema,
            errors=errors,
        )