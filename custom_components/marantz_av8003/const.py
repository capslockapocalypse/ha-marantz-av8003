"""Constants for the Marantz AV8003 integration."""

from marantz_rs232 import V2007Model, V2007Source

DOMAIN = "marantz_av8003"

CONF_HOST = "host"
CONF_PORT = "port"

DEFAULT_PORT = 8899
DEFAULT_NAME = "Marantz AV8003"

MODEL = V2007Model.AV8003

CONNECT_TIMEOUT = 5
RECONNECT_INTERVAL = 10

# Valid volume range for the v2007 protocol (see marantz_rs232.v2007.protocol.encode_volume).
MIN_VOLUME_DB = -80.0
MAX_VOLUME_DB = 18.0

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
