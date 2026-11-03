import asyncio

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumEntityFeature,
)

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([VR7Vacuum(coordinator)])


class VR7Vacuum(StateVacuumEntity):
    """Representation of the VR7 vacuum."""

    def __init__(self, coordinator):

        self.coordinator = coordinator
        self._attr_name = "Vorwerk VR7"

        self._attr_supported_features = (
            VacuumEntityFeature.START
            | VacuumEntityFeature.PAUSE
            | VacuumEntityFeature.RETURN_HOME
            | VacuumEntityFeature.STATE
        )
        self._attr_activity = None

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_start(self):
        """Start cleaning."""
        await self.coordinator.api.start_cleaning()

    async def async_pause(self):
        """Pause cleaning."""
        await self.coordinator.api.pause_cleaning()

    async def async_return_to_base(self):
        """Return to docking station."""
        await self.coordinator.api.pause_cleaning()
        await asyncio.sleep(2)
        await self.coordinator.api.dock()

