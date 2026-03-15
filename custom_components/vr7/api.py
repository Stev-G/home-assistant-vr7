import aiohttp
import logging

from .const import API_HOST

_LOGGER = logging.getLogger(__name__)


class VR7Api:

    def __init__(self, session, token):
        self.session = session
        self.token = token
        self.robot_id = None

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get_robots(self):

        url = f"{API_HOST}/dashboard"

        resp = await self.session.get(url, headers=self._headers())

        text = await resp.text()

        if resp.status != 200:
            _LOGGER.error(
                "Robot discovery failed status=%s response=%s",
                resp.status,
                text,
            )
            raise Exception("Robot discovery failed")

        data = await resp.json()

        robots = data.get("robots", [])

        if not robots:
            raise Exception("No robots found")

        return robots
    
    async def get_robot_id(self):

        if self.robot_id:
            return self.robot_id

        robots = await self.get_robots()

        self.robot_id = robots[0]["id"]

        _LOGGER.debug("VR7 robot discovered: %s", self.robot_id)

        return self.robot_id