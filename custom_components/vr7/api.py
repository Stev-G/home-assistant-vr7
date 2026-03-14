import aiohttp
from .const import API_HOST


class VR7Api:

    def __init__(self, token):
        self.token = token
        self.robot_id = None

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get_robots(self):

        async with aiohttp.ClientSession() as session:

            resp = await session.get(
                f"{API_HOST}/users/me/robots",
                headers=self._headers(),
            )

            data = await resp.json()

            if data:
                self.robot_id = data[0]["id"]

            return data

    async def start_cleaning(self):

        async with aiohttp.ClientSession() as session:

            await session.post(
                f"{API_HOST}/users/me/robots/{self.robot_id}/start",
                headers=self._headers(),
            )

    async def return_to_base(self):

        async with aiohttp.ClientSession() as session:

            await session.post(
                f"{API_HOST}/users/me/robots/{self.robot_id}/dock",
                headers=self._headers(),
            )