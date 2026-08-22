"""Diagnostic sensor platform for the Marantz AV8003 integration.

These are all read-only status fields the protocol reports but has no set
command for (input type, detected signal format, etc.).
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SAMPLING_FREQUENCY_LABELS, enum_label
from .coordinator import AV8003Connection
from .entity import AV8003Entity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    connection: AV8003Connection = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            AV8003InputTypeSensor(entry, connection),
            AV8003InputSignalSensor(entry, connection),
            AV8003InputStateSensor(entry, connection),
            AV8003SignalFormatSensor(entry, connection),
            AV8003SamplingFrequencySensor(entry, connection),
            AV8003ChannelStatusSensor(entry, connection),
            AV8003FirmwareVersionSensor(entry, connection),
        ]
    )


class _AV8003DiagnosticSensor(AV8003Entity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC


class AV8003InputTypeSensor(_AV8003DiagnosticSensor):
    _attr_name = "Input Type"
    _attr_icon = "mdi:import"

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "input_type")

    @property
    def native_value(self) -> str | None:
        value = self._live.input_ad
        return enum_label(value) if value is not None else None


class AV8003InputSignalSensor(_AV8003DiagnosticSensor):
    _attr_name = "Input Signal"
    _attr_icon = "mdi:signal"

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "input_signal")

    @property
    def native_value(self) -> str | None:
        value = self._live.input_signal
        return enum_label(value) if value is not None else None


class AV8003InputStateSensor(_AV8003DiagnosticSensor):
    _attr_name = "Input State"
    _attr_icon = "mdi:check-circle-outline"

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "input_state")

    @property
    def native_value(self) -> str | None:
        value = self._live.input_state
        return enum_label(value) if value is not None else None


class AV8003SignalFormatSensor(_AV8003DiagnosticSensor):
    _attr_name = "Signal Format"
    _attr_icon = "mdi:waveform"

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "signal_format")

    @property
    def native_value(self) -> str | None:
        value = self._live.signal_format
        return enum_label(value) if value is not None else None


class AV8003SamplingFrequencySensor(_AV8003DiagnosticSensor):
    _attr_name = "Sampling Frequency"
    _attr_icon = "mdi:sine-wave"

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "sampling_frequency")

    @property
    def native_value(self) -> str | None:
        value = self._live.sampling_frequency
        if value is None:
            return None
        return SAMPLING_FREQUENCY_LABELS.get(value.name, enum_label(value))


class AV8003ChannelStatusSensor(_AV8003DiagnosticSensor):
    _attr_name = "Channel Status (Raw)"
    _attr_icon = "mdi:information-outline"
    _attr_entity_registry_enabled_default = False

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "channel_status_raw")

    @property
    def native_value(self) -> str | None:
        return self._live.channel_status_raw


class AV8003FirmwareVersionSensor(_AV8003DiagnosticSensor):
    _attr_name = "Firmware Version"
    _attr_icon = "mdi:chip"

    def __init__(self, entry: ConfigEntry, connection: AV8003Connection) -> None:
        super().__init__(entry, connection, "firmware_version")

    @property
    def native_value(self) -> str | None:
        return self._live.firmware_version
