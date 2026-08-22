"""Media player platform for the Marantz AV8003 integration."""

from __future__ import annotations

import logging
import math

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from marantz_rs232 import V2007ReceiverState

from .const import DOMAIN, MAX_VOLUME_DB, MIN_VOLUME_DB, SOURCE_LABELS, SOURCE_LABELS_REVERSE
from .coordinator import AV8003Connection

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Marantz AV8003 media player from a config entry."""
    connection: AV8003Connection = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MarantzAV8003MediaPlayer(entry, connection)])


class MarantzAV8003MediaPlayer(MediaPlayerEntity):
    """Representation of a Marantz AV8003 main zone.

    Reads through to the live `marantz_rs232` receiver state rather than
    caching a local copy, so it's always consistent with the coordinator.
    """

    _attr_should_poll = False
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )
    _attr_source_list = list(SOURCE_LABELS.values())

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        self._entry = entry
        self._connection = connection
        self._main = connection.receiver.main
        self._attr_unique_id = entry.unique_id or entry.entry_id
        self._attr_name = entry.data.get(CONF_NAME)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=entry.data.get(CONF_NAME),
            manufacturer="Marantz",
            model="AV8003",
        )
        self._attr_available = connection.connected

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._connection.receiver.subscribe(self._handle_state))

    def _handle_state(self, state: V2007ReceiverState | None) -> None:
        self._attr_available = state is not None
        if self.hass is not None:
            self.async_write_ha_state()

    @property
    def state(self) -> MediaPlayerState | None:
        power = self._main.power
        if power is None:
            return None
        return MediaPlayerState.ON if power else MediaPlayerState.OFF

    @property
    def is_volume_muted(self) -> bool | None:
        return self._main.mute

    @property
    def volume_level(self) -> float | None:
        db = self._main.volume
        if db is None:
            return None
        if math.isinf(db):
            return 0.0
        span = MAX_VOLUME_DB - MIN_VOLUME_DB
        return max(0.0, min(1.0, (db - MIN_VOLUME_DB) / span))

    @property
    def source(self) -> str | None:
        source = self._main.input_source
        if source is None:
            return None
        return SOURCE_LABELS.get(source)

    async def async_turn_on(self) -> None:
        await self._main.power_on()

    async def async_turn_off(self) -> None:
        await self._main.power_off()

    async def async_volume_up(self) -> None:
        await self._main.volume_up()

    async def async_volume_down(self) -> None:
        await self._main.volume_down()

    async def async_set_volume_level(self, volume: float) -> None:
        db = MIN_VOLUME_DB + volume * (MAX_VOLUME_DB - MIN_VOLUME_DB)
        await self._main.set_volume(db)

    async def async_mute_volume(self, mute: bool) -> None:
        if mute:
            await self._main.mute_on()
        else:
            await self._main.mute_off()

    async def async_select_source(self, source: str) -> None:
        code = SOURCE_LABELS_REVERSE.get(source)
        if code is None:
            _LOGGER.warning("Unknown source: %s", source)
            return
        await self._main.select_source(code)
