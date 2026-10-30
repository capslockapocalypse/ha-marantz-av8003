"""Constants for the Marantz AV8003 integration."""

from marantz_rs232 import (
    V2007HDMIAudioMode,
    V2007HDMIChannel,
    V2007Model,
    V2007NightMode,
    V2007Source,
    V2007SurroundCode,
)

DOMAIN = "marantz_av8003"

CONF_HOST = "host"
CONF_PORT = "port"

DEFAULT_PORT = 8899
DEFAULT_NAME = "Marantz AV8003"

MODEL = V2007Model.AV8003

CONNECT_TIMEOUT = 5
RECONNECT_INTERVAL = 10
# Seconds between liveness checks, and how many missed replies mean the link is dead.
HEARTBEAT_INTERVAL = 30
HEARTBEAT_MAX_FAILURES = 2

# Valid volume/tone ranges for the v2007 protocol (see marantz_rs232.v2007.protocol).
MIN_VOLUME_DB = -80.0
MAX_VOLUME_DB = 18.0
MIN_TONE_DB = -6
MAX_TONE_DB = 6
MAX_SLEEP_MINUTES = 120

# Friendly labels for the wire-code sources the AV8003 actually accepts
# (marantz_rs232.v2007.const.V2007_SUPPORTED_SOURCES[V2007Model.AV8003]).
SOURCE_LABELS: dict[V2007Source, str] = {
    V2007Source.TV: "TV",
    V2007Source.DVD: "DVD",
    V2007Source.VCR1: "VCR 1",
    V2007Source.VCR2: "VCR 2",
    V2007Source.DSS_VCR2: "DSS/VCR2",
    V2007Source.NETWORK: "Network",
    V2007Source.AUX1: "Aux",
    V2007Source.CD_CDR: "CD/CD-R",
    V2007Source.TAPE: "Tape",
    V2007Source.TUNER1: "Tuner",
    V2007Source.FM1: "FM",
    V2007Source.AM1: "AM",
    V2007Source.XM1: "XM",
    V2007Source.SIRIUS: "Sirius",
}
SOURCE_LABELS_REVERSE = {v: k for k, v in SOURCE_LABELS.items()}

# Surround mode status codes -> friendly labels. Built from the full enum since
# every status code is also a valid direct-set code (unlike e.g. night mode's
# TOGGLE, there's no set-only pseudo-value to exclude here).
SURROUND_OPTIONS: dict[V2007SurroundCode, str] = {
    member: member.name.replace("_", " ").title() for member in V2007SurroundCode
}
SURROUND_OPTIONS_REVERSE = {v: k for k, v in SURROUND_OPTIONS.items()}

# HDMI output select. TOGGLE is a set-only pseudo-value with no matching status
# code, so it's excluded from the option list.
HDMI_OUTPUT_OPTIONS: dict[V2007HDMIChannel, str] = {
    V2007HDMIChannel.CH1: "HDMI 1",
    V2007HDMIChannel.CH2: "HDMI 2",
}
HDMI_OUTPUT_OPTIONS_REVERSE = {v: k for k, v in HDMI_OUTPUT_OPTIONS.items()}

HDMI_AUDIO_OPTIONS: dict[V2007HDMIAudioMode, str] = {
    V2007HDMIAudioMode.ENABLE: "Amplifier",
    V2007HDMIAudioMode.THROUGH: "TV (Passthrough)",
}
HDMI_AUDIO_OPTIONS_REVERSE = {v: k for k, v in HDMI_AUDIO_OPTIONS.items()}

# Night mode select. TOGGLE excluded for the same reason as HDMI output.
NIGHT_MODE_OPTIONS: dict[V2007NightMode, str] = {
    V2007NightMode.OFF: "Off",
    V2007NightMode.ON: "On",
    V2007NightMode.AUTO: "Auto",
}
NIGHT_MODE_OPTIONS_REVERSE = {v: k for k, v in NIGHT_MODE_OPTIONS.items()}

# Nicer labels than the raw enum names for the sampling-frequency diagnostic sensor.
SAMPLING_FREQUENCY_LABELS = {
    "OUT_OF_RANGE": "Out of Range",
    "HZ_32K": "32 kHz",
    "HZ_44_1K": "44.1 kHz",
    "HZ_48K": "48 kHz",
    "HZ_88_2K": "88.2 kHz",
    "HZ_96K": "96 kHz",
    "HZ_176_4K": "176.4 kHz",
    "HZ_192K": "192 kHz",
    "ANALOG": "Analog",
}


def enum_label(member) -> str:
    """Generic human-readable label for an enum member, e.g. DD_AC3 -> 'Dd Ac3'."""
    return member.name.replace("_", " ").title()
