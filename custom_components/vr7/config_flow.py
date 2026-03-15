import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_OTP,
    CONF_TOKEN,
    CONF_MARKET,
    DEFAULT_MARKET,
    AUTH_HOST,
)

_LOGGER = logging.getLogger(__name__)


SUPPORTED_MARKETS = {
    "DE": {"locale": "de-DE"},
    "EN": {"locale": "en-US"},
}

MARKET_OPTIONS = list(SUPPORTED_MARKETS.keys())


class VR7ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    email = None
    market = DEFAULT_MARKET

    async def async_step_user(self, user_input=None):

        errors = {}

        if user_input is not None:

            self.email = user_input[CONF_EMAIL]
            self.market = user_input[CONF_MARKET]

            try:

                session = async_get_clientsession(self.hass)

                market_settings = SUPPORTED_MARKETS[self.market]

                await session.post(
                    f"{AUTH_HOST}/passwordless/start",
                    json={
                        "connection": "email",
                        "email": self.email,
                        "send": "code",
                        "authParams": {
                            "scope": "openid profile email",
                            "ui_locales": market_settings["locale"],
                        },
                    },
                )

                return await self.async_step_otp()

            except Exception as err:
                _LOGGER.error("OTP send failed: %s", err)
                errors["base"] = "cannot_send_otp"

        schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_MARKET, default=self.market): vol.In(
                    MARKET_OPTIONS
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_otp(self, user_input=None):

        errors = {}

        if user_input is not None:

            try:

                session = async_get_clientsession(self.hass)

                resp = await session.post(
                    f"{AUTH_HOST}/oauth/token",
                    json={
                        "grant_type": "http://auth0.com/oauth/grant-type/passwordless/otp",
                        "username": self.email,
                        "otp": user_input[CONF_OTP],
                        "realm": "email",
                        "scope": "openid profile email",
                    },
                )

                text = await resp.text()

                if resp.status != 200:
                    _LOGGER.error("OTP validation error %s: %s", resp.status, text)
                    errors["base"] = "invalid_otp"
                else:
                    data = await resp.json()
                    token = data["access_token"]

                    return self.async_create_entry(
                        title="Vorwerk VR7",
                        data={
                            CONF_EMAIL: self.email,
                            CONF_TOKEN: token,
                        },
                    )

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

        schema = vol.Schema(
            {
                vol.Required(CONF_OTP): str,
            }
        )

        return self.async_show_form(
            step_id="otp",
            data_schema=schema,
            errors=errors,
        )