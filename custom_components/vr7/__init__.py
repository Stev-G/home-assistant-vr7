from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VR7Api
from .coordinator import VR7Coordinator
from .const import CONF_ID_TOKEN, CONF_MARKET, CONF_TOKEN, DEFAULT_MARKET, DOMAIN


PLATFORMS = ["vacuum", "sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):

    session = async_get_clientsession(hass)

    api = VR7Api(
        session,
        entry.data.get(CONF_ID_TOKEN) or entry.data[CONF_TOKEN],
        market=entry.data.get(CONF_MARKET, DEFAULT_MARKET),
    )

    coordinator = VR7Coordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
