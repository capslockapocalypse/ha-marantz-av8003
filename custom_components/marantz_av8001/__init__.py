"""The Marantz AV8001 integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN
from .protocol import AV8001Client

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]


def signal_update(entry_id: str) -> str:
    """Return the dispatcher signal used to push protocol lines to the entity."""
    return f"{DOMAIN}_{entry_id}_update"


def signal_connection(entry_id: str) -> str:
    """Return the dispatcher signal used to push connection state to the entity."""
    return f"{DOMAIN}_{entry_id}_connection"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Marantz AV8001 from a config entry."""
    update_signal = signal_update(entry.entry_id)
    connection_signal = signal_connection(entry.entry_id)
    client = AV8001Client(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        lambda line: async_dispatcher_send(hass, update_signal, line),
        lambda connected: async_dispatcher_send(hass, connection_signal, connected),
    )
    client.start()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        client: AV8001Client = hass.data[DOMAIN].pop(entry.entry_id)
        await client.stop()
    return unload_ok
