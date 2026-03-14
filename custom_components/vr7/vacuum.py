from homeassistant.components.vacuum import VacuumEntity
from homeassistant.components.vacuum import VacuumEntityFeature

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([VR7Vacuum(coordinator)])


class VR7Vacuum(VacuumEntity):
    """Representation of the VR7 vacuum."""

    def __init__(self, coordinator):

        self.coordinator = coordinator
        self._attr_name = "Vorwerk VR7"

        self._attr_supported_features = (
            VacuumEntityFeature.START
            | VacuumEntityFeature.RETURN_HOME
        )

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_start(self):
        """Start cleaning."""
        await self.coordinator.api.start_cleaning()

    async def async_return_to_base(self):
        """Return to docking station."""
        await self.coordinator.api.return_to_base()