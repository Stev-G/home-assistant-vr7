from unittest.mock import AsyncMock

import pytest

from custom_components.vr7.api import VR7Api
from custom_components.vr7.const import COMP_HOST


class FakeResponse:
    def __init__(self, *, status=200, headers=None, body=None):
        self.status = status
        self.headers = headers or {}
        self.body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def text(self):
        return "" if self.body is None else "{}"

    async def json(self):
        return self.body


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return self.response


@pytest.mark.asyncio
async def test_companion_login_returns_authorization_header():
    session = FakeSession(
        FakeResponse(headers={"Authorization": "Bearer companion-token"})
    )
    api = VR7Api(session, "orbital-token", id_token="auth0-id-token")

    authorization = await api.get_companion_authorization()

    method, url, kwargs = session.calls[0]
    assert method == "POST"
    assert url == f"{COMP_HOST}/api/v1/profile/login"
    assert kwargs["headers"]["Authorization"] == "Bearer auth0-id-token"
    assert authorization == "Bearer companion-token"


@pytest.mark.asyncio
async def test_start_cleaning_uses_cleaning_v2_payload():
    session = FakeSession(FakeResponse(body={}))
    api = VR7Api(session, "orbital-token")
    api.robot_id = "robot-id"
    api._request = AsyncMock(return_value={})

    await api.start_cleaning()

    api._request.assert_awaited_once_with(
        "POST",
        "/robots/robot-id/cleaning/v2",
        json={
            "runs": [
                {
                    "settings": {
                        "mode": "auto",
                        "navigation_mode": "normal",
                    },
                    "map": None,
                }
            ],
            "ability": "cleaning.start",
        },
        additional_headers={
            "mobile-app-version": "3.9.0",
            "mobile-app-build": "37883",
            "mobile-app-os": "android",
            "mobile-app-os-version": "11",
        },
    )
    assert api._headers()["Authorization"] == "Auth0Bearer orbital-token"


@pytest.mark.parametrize(
    ("method_name", "ability"),
    [
        ("pause_cleaning", "cleaning.pause"),
        ("resume_cleaning", "cleaning.resume"),
        ("dock", "navigation.return_to_base"),
    ],
)
@pytest.mark.asyncio
async def test_robot_message_commands_use_serial_number(method_name, ability):
    api = VR7Api(FakeSession(FakeResponse(body={})), "orbital-token")
    api.robot_id = "robot-id"
    api.robot_serial = "serial-number"
    api._request = AsyncMock(return_value={})

    await getattr(api, method_name)()

    api._request.assert_awaited_once_with(
        "POST",
        "/vendors/3/robots/serial-number/messages",
        json={"ability": ability},
    )
