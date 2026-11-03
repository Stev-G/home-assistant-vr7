import logging
from typing import List, Dict, Any, Optional

from .const import DEFAULT_MARKET, ORBITAL_HOST, SUPPORTED_MARKETS

_LOGGER = logging.getLogger(__name__)


class VR7Api:
    """API client for Vorwerk VR7."""

    def __init__(self, session, token, market=DEFAULT_MARKET):
        """Initialize API client."""
        self.session = session
        self.token = token
        self.market = market
        self.robot_id = None
        self.robot_serial = None

    def _headers(self):
        """Return headers for Vorwerk API requests."""
        return {
            "Authorization": f"Auth0Bearer {self.token}",
            "accept": "application/vnd.neato.orbital-http.v1+json",
            "user-agent": "okhttp/4.12.0",
            "Content-Type": "application/json",
            "accept-language": SUPPORTED_MARKETS.get(
                self.market, SUPPORTED_MARKETS[DEFAULT_MARKET]
            )["accept_language"],
        }

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make a request to the Vorwerk Orbital API."""
        headers = self._headers()
        if additional_headers:
            headers.update(additional_headers)

        url = f"{ORBITAL_HOST}{path}"
        _LOGGER.debug("VR7 API request %s %s", method, url)

        async with self.session.request(
            method, url, json=json, headers=headers
        ) as response:
            text = await response.text()
            if not 200 <= response.status < 300:
                _LOGGER.error(
                    "VR7 API error method=%s path=%s status=%s response=%s",
                    method,
                    path,
                    response.status,
                    text,
                )
                raise Exception(
                    f"VR7 API request failed with status {response.status}"
                )

            if not text:
                return None
            return await response.json()

    async def get_robots(self):
        """Fetch robots for current user."""

        data = await self._request(
            "GET",
            "/users/me/robots",
        )

        if not data:
            raise Exception("No robots found")

        return data

    async def get_robot_id(self):
        """Return robot id, fetch robots if needed."""

        if self.robot_id:
            return self.robot_id

        robots = await self.get_robots()

        robot = robots[0]
        self.robot_id = robot["id"]
        self.robot_serial = robot.get("serial") or robot.get("serial_number")

        _LOGGER.debug("VR7 robot discovered: %s", self.robot_id)

        return self.robot_id

    async def get_robot_state(self):
        """Fetch robot state."""

        robot_id = await self.get_robot_id()

        return await self._request(
            "GET",
            f"/robots/{robot_id}/state",
        )

    async def start_cleaning(self):
        """Start cleaning."""

        robot_id = await self.get_robot_id()

        return await self._request(
            "POST",
            f"/robots/{robot_id}/cleaning/v2",
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

    async def pause_cleaning(self):
        """Pause cleaning."""

        await self.get_robot_id()
        robot_serial = self.robot_serial
        if not robot_serial:
            raise Exception("VR7 robot serial number is missing")
        return await self._request(
            "POST",
            f"/vendors/3/robots/{robot_serial}/messages",
            json={"ability": "cleaning.pause"},
        )

    async def dock(self):
        """Send robot to dock."""

        await self.get_robot_id()
        robot_serial = self.robot_serial
        if not robot_serial:
            raise Exception("VR7 robot serial number is missing")
        return await self._request(
            "POST",
            f"/vendors/3/robots/{robot_serial}/messages",
            json={"ability": "navigation.return_to_base"},
        )
