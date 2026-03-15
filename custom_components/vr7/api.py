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

        url = f"{API_HOST}/users/me/robots"

        resp = await self.session.get(url, headers=self._headers())

        if resp.status != 200:
            text = await resp.text()
            _LOGGER.error("Robot discovery failed %s %s", resp.status, text)
            raise Exception("Robot discovery failed")

        data = await resp.json()

        if not data:
            raise Exception("No robots found")

        self.robot_id = data[0]["id"]

        return data