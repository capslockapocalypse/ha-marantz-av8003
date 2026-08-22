# Marantz AV8003 for Home Assistant

A custom Home Assistant integration to control a Marantz AV8003 pre-amp/processor
through an RS232-to-IP gateway (e.g. a USR-TCP232, Elfin, Moxa NPort, or similar
transparent serial-to-TCP bridge).

## Status

Power, volume, mute, and input select are implemented for the main zone as a
`media_player` entity, built on the [`marantz-rs232`](https://github.com/home-assistant-libs/marantz-rs232)
library. **Verified working against a real AV8003** over its RS232-to-IP
gateway — see [Protocol](#protocol) below.

## Requirements

- An RS232-to-IP gateway wired to the AV8003's RS-232 port, configured for
  **9600 baud, 8 data bits, no parity, 1 stop bit** (the AV8003's fixed
  serial settings), and set to bridge that serial port to a TCP port on your
  network in raw/transparent passthrough mode (not Telnet option
  negotiation, not RFC2217).
- The gateway's IP address and TCP port (commonly `8899` for this class of
  device — that's the default this integration suggests, but confirm on
  your gateway).

## Installation

### HACS (custom repository)

1. HACS → Integrations → ⋮ → Custom repositories → add this repo URL as an
   "Integration".
2. Install "Marantz AV8003", restart Home Assistant.

### Manual

Copy `custom_components/marantz_av8003` into your Home Assistant
`config/custom_components/` directory and restart.

## Setup

Settings → Devices & Services → Add Integration → "Marantz AV8003". You'll be
asked for a name, the gateway's **IP address**, and **port**.

## Protocol

The AV8003 (2009) does **not** use the shared Denon/Marantz `PW`/`MV`/`SI`
ASCII protocol used by same-era Denon models — it speaks Marantz's older,
distinct **"legacy" protocol** from the 2001–2010 SR-series lineage, framed
as `@CMD:VALUE\r` (e.g. `@PWR:2\r` for power on, `@VOL:?\r` to query
volume). This was initially built against the wrong (Denon-shared) protocol;
that was corrected after finding
[`home-assistant-libs/marantz-rs232`](https://github.com/home-assistant-libs/marantz-rs232),
which documents the AV8003 explicitly under its `v2007` protocol module, and
confirming it empirically — connecting to the real gateway and getting
coherent responses (`@PWR:2`, `@VOL: 00`, `@SRC:11`, etc.) that matched the
library's decoding exactly.

This integration depends on `marantz-rs232` (declared in `manifest.json`)
rather than reimplementing the protocol. It talks to the gateway over
`serialx`'s `socket://host:port` transport, which treats a raw TCP
connection as if it were a local serial port — a good fit for these
RS232-to-IP bridges.

Core commands used, via the library's `V2007MainPlayer`:

| Function     | Wire command                         |
|--------------|---------------------------------------|
| Power on/off | `@PWR:2` / `@PWR:1` / query `@PWR:?`  |
| Volume       | `@VOL:1` (up) / `@VOL:2` (down) / `@VOL:0xxxy` (set) / query `@VOL:?` |
| Mute         | `@AMT:2` / `@AMT:1` / query `@AMT:?`  |
| Input select | `@SRC:<code>` / query `@SRC:?`        |

The source list in `const.py` (`SOURCE_LABELS`) is restricted to the codes
the library documents as valid for the AV8003 specifically (TV, DVD, VCR1,
VCR2, DSS/VCR2, Network, Aux, CD/CD-R, Tape, Tuner, FM, AM, XM, Sirius).

Not yet implemented, but trivially available via the library's
`V2007MainPlayer` once there's appetite for it:
- Zone 2/3 (Multi Room A/B) power, volume, source, mute
- Surround mode select and cycling
- Bass/treble, night mode, sleep timer, HDMI channel/audio routing
- Tuner control, HD Radio metadata

## Development notes

- `coordinator.py` wraps `marantz_rs232.MarantzV2007Receiver` with a
  reconnect loop — the library itself is a connect-once client and doesn't
  retry on its own, so a gateway reboot or network blip would otherwise
  require reloading the config entry.
- `media_player.py` reads straight through to the live receiver state
  (`connection.receiver.main`) rather than caching a local copy, and
  subscribes to the receiver's push notifications so the entity updates
  immediately on state changes (including ones caused by someone using the
  physical remote) rather than polling.
