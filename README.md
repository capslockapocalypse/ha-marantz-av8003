# Marantz AV8003 for Home Assistant

A custom Home Assistant integration to control a Marantz AV8003 pre-amp/processor
through an RS232-to-IP gateway (e.g. Global Cache, Moxa NPort, USR-TCP232, or
similar transparent serial-to-TCP bridge).

## Status

Early scaffold. Power, volume, mute and input select are implemented for the
main zone as a `media_player` entity. **The command set has not yet been
verified against a real AV8003** — see [Protocol](#protocol) below.

## Requirements

- An RS232-to-IP gateway wired to the AV8003's RS-232 port, configured for
  **9600 baud, 8 data bits, no parity, 1 stop bit** (the AV8003's fixed
  serial settings), and set to bridge that serial port to a TCP port on your
  network (raw/transparent mode, not Telnet negotiation).
- The gateway's IP address and TCP port.

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

The AV8003 (2009) uses the ASCII serial command protocol shared across
Denon/Marantz AV receivers and processors of that generation (2-letter
COMMAND + PARAMETER, terminated with CR `0x0D`, e.g. `PWON\r`). This
integration was built against the documented protocol for its Denon sibling
**AVR-4310CI / AVC-4310** (D&M Holdings "DENON AVR control protocol
Ver. 6.3.0.a", released 21.Apr.'09, updated 02.Mar.'10) — the AVC-4310 is the
same 9.1-channel pre-amp/processor platform as the AV8003 (HDMI 1.3a, dual
HDMI outputs, Audyssey MultEQ XT). Core commands implemented:

| Function     | Command                          |
|--------------|-----------------------------------|
| Power on/off | `PWON` / `PWSTANDBY` / `PW?`      |
| Volume       | `MVUP` / `MVDOWN` / `MV**` / `MV?`|
| Mute         | `MUON` / `MUOFF` / `MU?`          |
| Input select | `SI<source>` / `SI?`              |

If you find an AV8003-specific RS232 protocol document, please compare it
against `custom_components/marantz_av8003/const.py` and
`custom_components/marantz_av8003/media_player.py` — command codes,
especially the input source list, may need adjusting for what's actually
wired on your unit (note this generation splits the older `TV/CBL` source
into separate `TV` and `SAT/CBL` codes).

Not yet implemented, but supported by the shared protocol and straightforward
to add once confirmed against the real unit:
- Zone 2 / Zone 3 power, volume, mute (`Z2`, `Z3` commands)
- Surround/sound mode select (`MS` command)
- Tone controls and Audyssey MultEQ XT / Dynamic EQ / Dynamic Volume
  (`PS` commands)
- HDMI output routing and resolution scaling (`VS` commands)

## Development notes

- `protocol.py` holds a transport-agnostic asyncio TCP client with automatic
  reconnect; it has no Home Assistant imports so it can be unit tested
  standalone.
- `__init__.py` bridges the client's incoming lines and connection state to
  the entity via Home Assistant's dispatcher, so the entity updates
  immediately on unsolicited state changes from the AVR (e.g. someone using
  the physical remote) rather than polling.
