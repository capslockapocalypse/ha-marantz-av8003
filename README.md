# Marantz AV8003 for Home Assistant

A custom Home Assistant integration to control a Marantz AV8003 pre-amp/processor
through an RS232-to-IP gateway (e.g. a USR-TCP232, Elfin, Moxa NPort, or similar
transparent serial-to-TCP bridge).

## Status

Exposes the AV8003 as a Home Assistant **device** with a set of individual
control entities (not a `media_player`, which can't cleanly represent a
processor's full control surface). Built on the
[`marantz-rs232`](https://github.com/home-assistant-libs/marantz-rs232)
library. **Verified working against a real AV8003** over its RS232-to-IP
gateway — see [Protocol](#protocol) below.

### Entities

| Platform | Entity | Notes |
|---|---|---|
| `switch` | Power | |
| `switch` | Mute | |
| `number` | Volume | -80 to +18 dB, 0.5 dB steps |
| `number` | Bass | -6 to +6 dB |
| `number` | Treble | -6 to +6 dB |
| `number` | Sleep Timer | 0-120 minutes |
| `select` | Source | TV, DVD, VCR 1/2, DSS/VCR2, Network, Aux, CD/CD-R, Tape, Tuner, FM, AM, XM, Sirius |
| `select` | Surround Mode | ~30 modes reported by the receiver |
| `select` | HDMI Output | HDMI 1 / HDMI 2 |
| `select` | HDMI Audio Routing | Amplifier / TV (Passthrough) |
| `select` | Night Mode | Off / On / Auto |
| `sensor` (diagnostic) | Input Type, Input Signal, Input State, Signal Format, Sampling Frequency, Firmware Version | read-only |
| `sensor` (diagnostic, disabled by default) | Channel Status (Raw) | opaque raw value, enable manually if useful |

Not included (scoped out for now, single-zone setup): Zone 2/3, tuner
frequency/preset control, HD Radio metadata, test tone, menu/cursor
navigation, video mute, attenuator, 7.1ch input toggle, speaker A/B,
Dolby Headphone mode, EQ mode, MDAX, THX mode, interlace/progressive
converter, front key lock, DC triggers. All of these are already exposed by
the underlying library (`V2007MainPlayer`/`V2007MultiRoomPlayer`) and follow
the same pattern as the entities above, so adding any of them later is
mostly a matter of adding a class to the relevant platform file.

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
asked for a name, the gateway's **IP address**, and **port**. On startup, the
integration queries the full protocol state (~35 status queries sent
sequentially) — this can take several seconds, during which entities show as
unknown before populating.

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

Wire commands behind each entity group, via the library's `V2007MainPlayer`:

| Function | Wire command |
|---|---|
| Power | `@PWR:2` / `@PWR:1` / query `@PWR:?` |
| Mute | `@AMT:2` / `@AMT:1` / query `@AMT:?` |
| Volume | `@VOL:0xxxy` (set) / query `@VOL:?` |
| Bass / Treble | `@TOB:0xx` / `@TOT:0xx` / query `@TOB:?` / `@TOT:?` |
| Sleep timer | `@SLP:0xxx` / query `@SLP:?` |
| Source | `@SRC:<code>` / query `@SRC:?` |
| Surround mode | `@SUR:0<code>` / query `@SUR:?` |
| HDMI output | `@HDM:<1\|2>` / query `@HDM:?` |
| HDMI audio routing | `@HAM:<1\|2>` / query `@HAM:?` |
| Night mode | `@NGT:<1\|2\|3>` / query `@NGT:?` |
| Diagnostics | `@INP`/`@ISG`/`@IST`/`@SIG`/`@SFQ`/`@CHS`/`@RSV`, all query-only |

The source list in `const.py` (`SOURCE_LABELS`) is restricted to the codes
the library documents as valid for the AV8003 specifically.

## Development notes

- `coordinator.py` wraps `marantz_rs232.MarantzV2007Receiver` with a
  reconnect loop — the library itself is a connect-once client and doesn't
  retry on its own, so a gateway reboot or network blip would otherwise
  require reloading the config entry.
- `entity.py` holds a shared base class (`AV8003Entity`) that every platform
  entity inherits: device info, unique_id, availability, and subscribing to
  the receiver's push notifications. Entities read straight through to the
  live receiver state (`connection.receiver.main`, or `main._state` for the
  diagnostic fields the library doesn't expose as convenience properties)
  rather than caching a local copy, so they update immediately on state
  changes — including ones caused by someone using the physical remote —
  rather than polling.
