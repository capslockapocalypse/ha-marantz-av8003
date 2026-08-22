"""Switch platform for the Marantz AV8003 integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AV8003Connection
from .entity import AV8003Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    connection: AV8003Connection = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AV8003PowerSwitch(entry, connection),
            AV8003MuteSwitch(entry, connection),
        ]
    )


class AV8003PowerSwitch(AV8003Entity, SwitchEntity):
    _attr_name = "Power"
    _attr_icon = "mdi:power"

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "power")

    @property
    def is_on(self) -> bool | None:
        return self._main.power

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._main.power_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._main.power_off()


class AV8003MuteSwitch(AV8003Entity, SwitchEntity):
    _attr_name = "Mute"
    _attr_icon = "mdi:volume-mute"

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "mute")

    @property
    def is_on(self) -> bool | None:
        return self._main.mute

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._main.mute_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._main.mute_off()
