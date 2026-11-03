import asyncio

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)

from .const import DOMAIN
from .websocket import VR7WebSocket


async def async_setup_entry(hass, entry, async_add_entities):

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([VR7Vacuum(hass, coordinator)])


class VR7Vacuum(StateVacuumEntity):
    """Representation of the VR7 vacuum."""

    def __init__(self, hass, coordinator):

        self.hass = hass
        self.coordinator = coordinator
        self._attr_name = "Vorwerk VR7"

        self._attr_supported_features = (
            VacuumEntityFeature.START
            | VacuumEntityFeature.PAUSE
            | VacuumEntityFeature.RETURN_HOME
            | VacuumEntityFeature.STATE
        )
        self._attr_activity = None
        self._attr_status = None
        self._attr_available_commands = None
        self._status_client = VR7WebSocket(
            hass,
            coordinator.api.session,
            coordinator.api,
            coordinator.data["robot_id"],
            coordinator.api.market,
            self._handle_status_update,
        )

    async def async_added_to_hass(self):
        """Start receiving live robot status after entity registration."""
        await super().async_added_to_hass()
        self._status_client.start()

    async def async_will_remove_from_hass(self):
        """Stop the status connection when the entity is removed."""
        await self._status_client.stop()
        await super().async_will_remove_from_hass()

    def _handle_status_update(self, status):
        """Apply normalized status data received from the Companion service."""
        if status.get("activity") is not None:
            self._attr_activity = status["activity"]
        if status.get("status") is not None:
            self._attr_status = status["status"]
        if status.get("available_commands") is not None:
            self._attr_available_commands = status["available_commands"]
        self.async_write_ha_state()

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_start(self):
        """Start cleaning."""
        commands = self._attr_available_commands or {}
        if self._attr_activity == VacuumActivity.PAUSED and commands.get("resume"):
            await self.coordinator.api.resume_cleaning()
        else:
            await self.coordinator.api.start_cleaning()

    async def async_pause(self):
        """Pause cleaning."""
        await self.coordinator.api.pause_cleaning()

    async def async_return_to_base(self):
        """Return to docking station."""
        commands = self._attr_available_commands or {}
        if commands.get("return_to_base"):
            await self.coordinator.api.dock()
            return

        if self._attr_activity != VacuumActivity.PAUSED:
            if self._attr_available_commands is not None and not commands.get("pause"):
                await self.coordinator.api.dock()
                return
            await self.coordinator.api.pause_cleaning()
            await asyncio.sleep(2)
        await self.coordinator.api.dock()

