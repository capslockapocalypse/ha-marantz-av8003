"""Constants for the Marantz AV8003 integration."""

DOMAIN = "marantz_av8003"

CONF_HOST = "host"
CONF_PORT = "port"

DEFAULT_PORT = 23
DEFAULT_NAME = "Marantz AV8003"

# Connection / protocol timing
CONNECT_TIMEOUT = 5
COMMAND_TIMEOUT = 3
RECONNECT_INTERVAL = 10

# D&M Holdings ASCII serial protocol, shared by Denon/Marantz AV receivers
# and pre-amp/processors of this generation. Commands are terminated with CR (0x0D).
TERMINATOR = "\r"

# Master volume is sent as an offset where 80 == 0 dB, 00 == -80 dB, 98 == +18 dB.
MV_OFFSET = 80
MV_MIN = 0
MV_MAX = 98

# Input sources supported by the shared protocol (per the AVR-4310CI/AVC-4310
# reference, same generation as the AV8003). The AV8003 will only have a
# subset of these physically wired; unused ones are harmless to send/ignore.
SOURCES = {
    "PHONO": "Phono",
    "CD": "CD",
    "TUNER": "Tuner",
    "DVD": "DVD",
    "HDP": "HD Radio/HDP",
    "TV": "TV",
    "SAT/CBL": "Sat/Cbl",
    "VCR": "VCR",
    "DVR": "DVR",
    "V.AUX": "V.Aux",
    "IPOD": "iPod",
    "USB/IPOD": "USB/iPod",
}
SOURCES_REVERSE = {v: k for k, v in SOURCES.items()}
