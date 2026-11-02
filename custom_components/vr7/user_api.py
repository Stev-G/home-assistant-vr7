import logging
from .const import CLIENT_ID

_LOGGER = logging.getLogger(__name__)


class UserApiClient:

    def __init__(self, session, host, path_send_otp, path_validate_otp, language, accept_language):
        self.session = session
        self.host = host
        self.path_send_otp = path_send_otp
        self.path_validate_otp = path_validate_otp
        self.language = language
        self.accept_language = accept_language

    async def send_otp(self, email):

        url = f"{self.host}{self.path_send_otp}"

        payload = {
            "client_id": CLIENT_ID,
            "connection": "email",
            "email": email,
            "send": "code",
            "authParams": {
                "scope": "openid profile email",
                "ui_locales": self.accept_language
            }
        }

        headers = {
            "content-type": "application/json",
            "accept-language": self.accept_language,
        }
        async with self.session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                _LOGGER.error("OTP request failed with HTTP %s", resp.status)
                raise Exception("OTP request failed")

    async def validate_otp(self, email, otp):

        url = f"{self.host}{self.path_validate_otp}"

        payload = {
            "grant_type": "http://auth0.com/oauth/grant-type/passwordless/otp",
            "client_id": CLIENT_ID,
            "username": email,
            "otp": otp,
            "realm": "email",
            "scope": "openid profile email",
            "platform": "android",
            "locale": self.language,
            "source": "vorwerk_auth0" if self.language == "de" else "vorwerk_auth0_international",
        }

        headers = {
            "content-type": "application/json",
            "accept-language": self.accept_language,
        }
        async with self.session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                _LOGGER.error("OTP validation failed with HTTP %s", resp.status)
                raise Exception("OTP validation failed")
            return await resp.json()
