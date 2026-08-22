# Marantz AV8001 for Home Assistant

A custom Home Assistant integration to control a Marantz AV8001 pre-amp/processor
through an RS232-to-IP gateway (e.g. Global Cache, Moxa NPort, USR-TCP232, or
similar transparent serial-to-TCP bridge).

## Status

Early scaffold. Power, volume, mute and input select are implemented for the
main zone as a `media_player` entity. **The command set has not yet been
verified against a real AV8001** — see [Protocol](#protocol) below.

## Requirements

- An RS232-to-IP gateway wired to the AV8001's RS-232 port, configured for
  **9600 baud, 8 data bits, no parity, 1 stop bit** (the AV8001's fixed
  serial settings), and set to bridge that serial port to a TCP port on your
  network (raw/transparent mode, not Telnet negotiation).
- The gateway's IP address and TCP port.

## Installation

### HACS (custom repository)

1. HACS → Integrations → ⋮ → Custom repositories → add this repo URL as an
   "Integration".
2. Install "Marantz AV8001", restart Home Assistant.

### Manual

Copy `custom_components/marantz_av8001` into your Home Assistant
`config/custom_components/` directory and restart.

## Setup

Settings → Devices & Services → Add Integration → "Marantz AV8001". You'll be
asked for a name, the gateway's **IP address**, and **port**.

## Protocol

The AV8001 (2007) uses the ASCII serial command protocol shared across
Denon/Marantz AV receivers and processors of that generation (2-letter
COMMAND + PARAMETER, terminated with CR `0x0D`, e.g. `PWON\r`). This
integration was built against the documented protocol for the sibling
**AVR-4308 / AVC-4320** (D&M Holdings "DENON AVR control protocol Ver. 5.1",
2007/07/06), which is the same platform generation as the AV8001. Core
commands implemented:

| Function     | Command                          |
|--------------|-----------------------------------|
| Power on/off | `PWON` / `PWSTANDBY` / `PW?`      |
| Volume       | `MVUP` / `MVDOWN` / `MV**` / `MV?`|
| Mute         | `MUON` / `MUOFF` / `MU?`          |
| Input select | `SI<source>` / `SI?`              |

If you find an AV8001-specific RS232 protocol document, please compare it
against `custom_components/marantz_av8001/const.py` and
`custom_components/marantz_av8001/media_player.py` — command codes,
especially the input source list, may need adjusting for what the AV8001
actually supports (it predates HDMI-era additions like NET/USB and DAB).

Not yet implemented, but supported by the shared protocol and straightforward
to add once confirmed against the real unit:
- Zone 2 / Zone 3 power, volume, mute (`Z2`, `Z3` commands)
- Surround/sound mode select (`MS` command)
- Tone controls (`PS` commands: bass, treble, DRC, etc.)

## Development notes

- `protocol.py` holds a transport-agnostic asyncio TCP client with automatic
  reconnect; it has no Home Assistant imports so it can be unit tested
  standalone.
- `__init__.py` bridges the client's incoming lines and connection state to
  the entity via Home Assistant's dispatcher, so the entity updates
  immediately on unsolicited state changes from the AVR (e.g. someone using
  the physical remote) rather than polling.
