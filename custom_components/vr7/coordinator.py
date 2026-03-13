from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import SCAN_INTERVAL

class VR7Coordinator(DataUpdateCoordinator):
    """Coordinator für regelmäßige Status-Updates vom VR7."""

    def __init__(self, hass, api):
        super().__init__(
            hass,
            logger=None,  # optional: Logger einfügen
            name="VR7",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self):
        """Daten vom Roboter abrufen."""
        return await self.api.get_robot()