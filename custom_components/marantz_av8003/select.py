"""Select platform for the Marantz AV8003 integration."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from marantz_rs232 import V2007SurroundCode

from .const import (
    DOMAIN,
    HDMI_AUDIO_OPTIONS,
    HDMI_AUDIO_OPTIONS_REVERSE,
    HDMI_OUTPUT_OPTIONS,
    HDMI_OUTPUT_OPTIONS_REVERSE,
    NIGHT_MODE_OPTIONS,
    NIGHT_MODE_OPTIONS_REVERSE,
    SOURCE_LABELS,
    SOURCE_LABELS_REVERSE,
    SURROUND_OPTIONS,
    SURROUND_OPTIONS_REVERSE,
)
from .coordinator import AV8003Connection
from .entity import AV8003Entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    connection: AV8003Connection = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AV8003SourceSelect(entry, connection),
            AV8003SurroundModeSelect(entry, connection),
            AV8003HdmiOutputSelect(entry, connection),
            AV8003HdmiAudioSelect(entry, connection),
            AV8003NightModeSelect(entry, connection),
        ]
    )


class AV8003SourceSelect(AV8003Entity, SelectEntity):
    _attr_name = "Source"
    _attr_icon = "mdi:import"
    _attr_options = list(SOURCE_LABELS.values())

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "source")

    @property
    def current_option(self) -> str | None:
        source = self._main.input_source
        return SOURCE_LABELS.get(source) if source else None

    async def async_select_option(self, option: str) -> None:
        code = SOURCE_LABELS_REVERSE.get(option)
        if code is None:
            _LOGGER.warning("Unknown source option: %s", option)
            return
        await self._main.select_source(code)


class AV8003SurroundModeSelect(AV8003Entity, SelectEntity):
    _attr_name = "Surround Mode"
    _attr_icon = "mdi:surround-sound"
    _attr_options = list(SURROUND_OPTIONS.values())

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "surround_mode")

    @property
    def current_option(self) -> str | None:
        code = self._main.surround_mode
        if code is None:
            return None
        try:
            member = V2007SurroundCode(code)
        except ValueError:
            return None
        return SURROUND_OPTIONS.get(member)

    async def async_select_option(self, option: str) -> None:
        member = SURROUND_OPTIONS_REVERSE.get(option)
        if member is None:
            _LOGGER.warning("Unknown surround mode option: %s", option)
            return
        await self._main.set_surround_mode(member.value)


class AV8003HdmiOutputSelect(AV8003Entity, SelectEntity):
    _attr_name = "HDMI Output"
    _attr_icon = "mdi:hdmi-port"
    _attr_options = list(HDMI_OUTPUT_OPTIONS.values())

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "hdmi_output")

    @property
    def current_option(self) -> str | None:
        channel = self._main.hdmi_channel
        return HDMI_OUTPUT_OPTIONS.get(channel) if channel else None

    async def async_select_option(self, option: str) -> None:
        member = HDMI_OUTPUT_OPTIONS_REVERSE.get(option)
        if member is None:
            _LOGGER.warning("Unknown HDMI output option: %s", option)
            return
        await self._main.set_hdmi_channel(member)


class AV8003HdmiAudioSelect(AV8003Entity, SelectEntity):
    _attr_name = "HDMI Audio Routing"
    _attr_icon = "mdi:speaker"
    _attr_options = list(HDMI_AUDIO_OPTIONS.values())

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "hdmi_audio")

    @property
    def current_option(self) -> str | None:
        mode = self._main.hdmi_audio_mode
        return HDMI_AUDIO_OPTIONS.get(mode) if mode else None

    async def async_select_option(self, option: str) -> None:
        member = HDMI_AUDIO_OPTIONS_REVERSE.get(option)
        if member is None:
            _LOGGER.warning("Unknown HDMI audio option: %s", option)
            return
        await self._main.set_hdmi_audio_mode(member)


class AV8003NightModeSelect(AV8003Entity, SelectEntity):
    _attr_name = "Night Mode"
    _attr_icon = "mdi:weather-night"
    _attr_options = list(NIGHT_MODE_OPTIONS.values())

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "night_mode")

    @property
    def current_option(self) -> str | None:
        mode = self._main.night_mode
        return NIGHT_MODE_OPTIONS.get(mode) if mode else None

    async def async_select_option(self, option: str) -> None:
        member = NIGHT_MODE_OPTIONS_REVERSE.get(option)
        if member is None:
            _LOGGER.warning("Unknown night mode option: %s", option)
            return
        await self._main.set_night_mode(member)
