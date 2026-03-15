import logging
from typing import List, Dict, Any, Optional

from .const import COMP_HOST

_LOGGER = logging.getLogger(__name__)


class VR7Api:
    """API client for Vorwerk VR7."""

    def __init__(self, session, token):
        """Initialize API client."""
        self.session = session
        self.token = token
        self.robot_id = None

    def _headers(self):
        """Return headers for Vorwerk API requests."""
        return {
            "Authorization": f"Auth0Bearer {self.token}",
            "accept": "application/vnd.neato.orbital-http.v1+json",
            "user-agent": "okhttp/4.12.0",
            "Content-Type": "application/json",
        }

    async def _request(self, 
                       method: str, 
                       path: str,
                       json: Optional[Dict[str, Any]] = None,
                       additional_headers: Optional[Dict[str, str]] = None,
                       )-> Any:
                        headers = self._headers()
                        if additional_headers:
                            headers.update(additional_headers)  

                        """Make request to Vorwerk API."""

                        url = f"{COMP_HOST}{path}"

                        _LOGGER.debug("VR7 API request %s %s", method, url)

                        async with self.session.request(method, url, json=json, headers = headers) as response:

                            text = await response.text()

                            if response.status != 200:
                                _LOGGER.error(
                                    "VR7 API error status=%s response=%s",
                                    response.status,
                                    text,
                                )
                                raise Exception("VR7 API request failed")

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

        self.robot_id = robots[0]["id"]

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
            f"/robots/{robot_id}/cleaning/start",
        )

    async def pause_cleaning(self):
        """Pause cleaning."""

        robot_id = await self.get_robot_id()

        return await self._request(
            "POST",
            f"/robots/{robot_id}/cleaning/pause",
        )

    async def dock(self):
        """Send robot to dock."""

        robot_id = await self.get_robot_id()

        return await self._request(
            "POST",
            f"/robots/{robot_id}/dock",
        )