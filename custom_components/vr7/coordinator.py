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

    async def _async_update_data(self):

        robot_id = await self.api.get_robot_id()

        return {
            "robot_id": robot_id
        }