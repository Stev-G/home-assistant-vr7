import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class VR7Coordinator(DataUpdateCoordinator):

    def __init__(self, hass, api):
        self.api = api

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def get_robot_id(self):

        if self.robot_id:
            return self.robot_id

        robots = await self.get_robots()

        self.robot_id = robots[0]["id"]

        _LOGGER.debug("VR7 robot discovered: %s", self.robot_id)

        return self.robot_id