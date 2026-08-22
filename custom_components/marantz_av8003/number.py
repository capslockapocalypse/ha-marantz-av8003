"""Number platform for the Marantz AV8003 integration."""

from __future__ import annotations

import math

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MAX_SLEEP_MINUTES,
    MAX_TONE_DB,
    MAX_VOLUME_DB,
    MIN_TONE_DB,
    MIN_VOLUME_DB,
)
from .coordinator import AV8003Connection
from .entity import AV8003Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    connection: AV8003Connection = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AV8003VolumeNumber(entry, connection),
            AV8003BassNumber(entry, connection),
            AV8003TrebleNumber(entry, connection),
            AV8003SleepTimerNumber(entry, connection),
        ]
    )


class AV8003VolumeNumber(AV8003Entity, NumberEntity):
    _attr_name = "Volume"
    _attr_icon = "mdi:volume-high"
    _attr_native_min_value = MIN_VOLUME_DB
    _attr_native_max_value = MAX_VOLUME_DB
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "dB"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "volume")

    @property
    def native_value(self) -> float | None:
        db = self._main.volume
        if db is None or math.isinf(db):
            return None
        return db

    async def async_set_native_value(self, value: float) -> None:
        await self._main.set_volume(value)


class AV8003BassNumber(AV8003Entity, NumberEntity):
    _attr_name = "Bass"
    _attr_icon = "mdi:music-clef-bass"
    _attr_native_min_value = MIN_TONE_DB
    _attr_native_max_value = MAX_TONE_DB
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "dB"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "bass")

    @property
    def native_value(self) -> float | None:
        return self._main.bass

    async def async_set_native_value(self, value: float) -> None:
        await self._main.set_bass(int(value))


class AV8003TrebleNumber(AV8003Entity, NumberEntity):
    _attr_name = "Treble"
    _attr_icon = "mdi:music-clef-treble"
    _attr_native_min_value = MIN_TONE_DB
    _attr_native_max_value = MAX_TONE_DB
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "dB"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "treble")

    @property
    def native_value(self) -> float | None:
        return self._main.treble

    async def async_set_native_value(self, value: float) -> None:
        await self._main.set_treble(int(value))


class AV8003SleepTimerNumber(AV8003Entity, NumberEntity):
    _attr_name = "Sleep Timer"
    _attr_icon = "mdi:timer-outline"
    _attr_native_min_value = 0
    _attr_native_max_value = MAX_SLEEP_MINUTES
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "sleep_timer")

    @property
    def native_value(self) -> float | None:
        return self._main.sleep_minutes

    async def async_set_native_value(self, value: float) -> None:
        await self._main.set_sleep(int(value))
