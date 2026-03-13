from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import VR7Api
from .coordinator import VR7Coordinator
from .const import DOMAIN

PLATFORMS = ["vacuum", "sensor", "button"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up VR7 from a config entry."""

    # API-Client erstellen
    api = VR7Api(
        entry.data["email"],
        entry.data["password"],
    )

    # Login
    await api.login()

    # Coordinator erstellen
    coordinator = VR7Coordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    # Coordinator in hass.data speichern
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Plattformen laden
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True