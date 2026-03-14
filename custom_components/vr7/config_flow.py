import voluptuous as vol
import logging

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_EMAIL, CONF_OTP

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
                    "https://auth.ksecosys.com/passwordless/start",
                    json={
                        "email": self.email,
                        "connection": "email"
                    },
                )

                return await self.async_step_otp()

            except Exception as e:
                _LOGGER.error("OTP send error: %s", e)
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
        """Step 2: user enters OTP."""

        errors = {}

        if user_input is not None:
            otp = user_input[CONF_OTP]

            try:
                session = async_get_clientsession(self.hass)

                resp = await session.post(
                    "https://auth.ksecosys.com/oauth/token",
                    json={
                        "grant_type": "http://auth0.com/oauth/grant-type/passwordless/otp",
                        "username": self.email,
                        "otp": otp,
                        "realm": "email",
                        "scope": "openid profile email",
                    },
                )

                data = await resp.json()

                token = data["access_token"]

                return self.async_create_entry(
                    title="Vorwerk VR7",
                    data={
                        "email": self.email,
                        "token": token,
                    },
                )

            except Exception as e:
                _LOGGER.error("OTP validation error: %s", e)
                errors["base"] = "invalid_otp"

        schema = vol.Schema({
            vol.Required(CONF_OTP): str
        })

        return self.async_show_form(
            step_id="otp",
            data_schema=schema,
            errors=errors,
        )