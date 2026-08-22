"""Media player platform for the Marantz AV8001 integration."""

from __future__ import annotations

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import signal_connection, signal_update
from .const import DOMAIN, MV_MAX, MV_MIN, SOURCES, SOURCES_REVERSE
from .protocol import AV8001Client, AV8001Error

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Marantz AV8001 media player from a config entry."""
    client: AV8001Client = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MarantzAV8001MediaPlayer(entry, client)])


class MarantzAV8001MediaPlayer(MediaPlayerEntity):
    """Representation of a Marantz AV8001 main zone."""

    _attr_should_poll = False
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )
    _attr_source_list = list(SOURCES.values())

    def __init__(self, entry: ConfigEntry, client: AV8001Client) -> None:
        self._entry = entry
        self._client = client
        self._attr_unique_id = entry.unique_id or entry.entry_id
        self._attr_name = entry.data.get(CONF_NAME)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=entry.data.get(CONF_NAME),
            manufacturer="Marantz",
            model="AV8001",
        )
        self._attr_state = MediaPlayerState.OFF
        self._attr_available = self._client.connected

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_update(self._entry.entry_id), self._handle_line
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                signal_connection(self._entry.entry_id),
                self._handle_connection,
            )
        )
        if self._client.connected:
            await self._async_refresh()

    @callback
    def _handle_connection(self, connected: bool) -> None:
        self._attr_available = connected
        self.async_write_ha_state()
        if connected:
            self.hass.async_create_task(self._async_refresh())

    async def _async_refresh(self) -> None:
        """Query current state after (re)connecting."""
        for command, prefix in (("PW?", "PW"), ("MV?", "MV"), ("MU?", "MU"), ("SI?", "SI")):
            try:
                response = await self._client.async_query(command, prefix)
            except AV8001Error:
                return
            if response:
                self._handle_line(response)

    @callback
    def _handle_line(self, line: str) -> None:
        """Parse a line pushed from the AV8001 and update entity state."""
        changed = True
        if line == "PWON":
            self._attr_state = MediaPlayerState.ON
        elif line == "PWSTANDBY":
            self._attr_state = MediaPlayerState.OFF
        elif line == "MUON":
            self._attr_is_volume_muted = True
        elif line == "MUOFF":
            self._attr_is_volume_muted = False
        elif line.startswith("MV") and not line.startswith("MVMAX") and line[2:].strip("0123456789") == "":
            param = line[2:]
            # A 3-digit parameter is a 0.5dB-step value, e.g. "805" == 80.5
            value = int(param) / 10 if len(param) == 3 else float(param)
            self._attr_volume_level = _mv_to_volume(value)
        elif line.startswith("SI"):
            source_code = line[2:]
            self._attr_source = SOURCES.get(source_code, source_code)
        else:
            changed = False

        self._attr_available = True
        if changed and self.hass is not None:
            self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        await self._client.async_send_command("PWON")

    async def async_turn_off(self) -> None:
        await self._client.async_send_command("PWSTANDBY")

    async def async_volume_up(self) -> None:
        await self._client.async_send_command("MVUP")

    async def async_volume_down(self) -> None:
        await self._client.async_send_command("MVDOWN")

    async def async_set_volume_level(self, volume: float) -> None:
        mv_value = round(MV_MIN + volume * (MV_MAX - MV_MIN))
        await self._client.async_send_command(f"MV{mv_value:02d}")

    async def async_mute_volume(self, mute: bool) -> None:
        await self._client.async_send_command("MUON" if mute else "MUOFF")

    async def async_select_source(self, source: str) -> None:
        source_code = SOURCES_REVERSE.get(source)
        if source_code is None:
            _LOGGER.warning("Unknown source: %s", source)
            return
        await self._client.async_send_command(f"SI{source_code}")


def _mv_to_volume(mv_value: float) -> float:
    """Convert a raw MV parameter (0-98, half-steps allowed) to a 0.0-1.0 HA volume level."""
    clamped = max(MV_MIN, min(MV_MAX, mv_value))
    return (clamped - MV_MIN) / (MV_MAX - MV_MIN)
