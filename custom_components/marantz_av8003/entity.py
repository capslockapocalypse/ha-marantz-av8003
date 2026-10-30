"""Shared base for Marantz AV8003 entities."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import DeviceInfo, Entity
from marantz_rs232 import V2007ReceiverState

from .const import DOMAIN
from .coordinator import AV8003Connection


class AV8003Entity(Entity):
    """Common wiring for all Marantz AV8003 entities.

    Handles device info, unique_id, availability, and live push updates —
    every entity reads straight through to the coordinator's receiver state
    rather than caching its own copy.
    """

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection, key: str) -> None:
        self._entry = entry
        self._connection = connection
        self._main = connection.receiver.main
        # V2007MainPlayer doesn't expose every field as a convenience property
        # (e.g. the diagnostic-only ones). `main._state` is the same live
        # V2007MainState instance the receiver mutates in place, so reading it
        # directly still gets fresh values — see marantz_rs232.v2007.players.
        self._live = connection.receiver.main._state
        device_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=entry.data.get(CONF_NAME),
            manufacturer="Marantz",
            model="AV8003",
        )
        self._attr_available = connection.connected

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._connection.subscribe(self._handle_state))

    def _handle_state(self, state: V2007ReceiverState | None) -> None:
        self._attr_available = state is not None
        if self.hass is not None:
            self.async_write_ha_state()
