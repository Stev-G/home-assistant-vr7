import aiohttp

class VR7Api:
    """Minimaler VR7 API Client."""

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.token = None
        self.robot_id = None

    async def login(self):
        """Login in die Vorwerk Cloud."""
        async with aiohttp.ClientSession() as session:
            r = await session.post(
                "https://beehive.ksecosys.com/dashboard",
                json={
                    "email": self.email,
                    "password": self.password,
                    "platform": "ios"
                }
            )
            data = await r.json()
            self.token = data["access_token"]

    async def get_robot(self):
        """Erste Roboter-ID abrufen."""
        headers = {"Authorization": f"Bearer {self.token}"}
        async with aiohttp.ClientSession() as session:
            r = await session.get(
                "https://beehive.ksecosys.com/users/me/robots",
                headers=headers
            )
            robots = await r.json()
            self.robot_id = robots[0]["id"]
            return robots[0]