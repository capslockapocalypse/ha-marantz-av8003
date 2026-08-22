"""Async TCP client for a Marantz AV8001 connected via an RS232-to-IP gateway.

The gateway is assumed to be a transparent serial-to-TCP bridge (e.g. a Global
Cache, Moxa NPort, USR-TCP232, etc.) that simply forwards raw bytes to/from the
AVR's RS-232 port. The AVR itself speaks the D&M Holdings ASCII command
protocol shared by Denon/Marantz receivers and pre-amp/processors of this
generation: 2-letter COMMAND + PARAMETER, terminated with CR (0x0D).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable

from .const import COMMAND_TIMEOUT, CONNECT_TIMEOUT, RECONNECT_INTERVAL, TERMINATOR

_LOGGER = logging.getLogger(__name__)

UpdateCallback = Callable[[str], None]
ConnectionCallback = Callable[[bool], None]


class AV8001Error(Exception):
    """Raised for AV8001 client errors."""


class AV8001Client:
    """Maintains a persistent connection to the RS232-IP gateway."""

    def __init__(
        self,
        host: str,
        port: int,
        update_callback: UpdateCallback,
        connection_callback: ConnectionCallback | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._update_callback = update_callback
        self._connection_callback = connection_callback

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._run_task: asyncio.Task | None = None
        self._stopping = False

        self._pending: dict[str, asyncio.Future] = {}

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    def start(self) -> None:
        """Start the background connect/read loop."""
        self._stopping = False
        if self._run_task is None or self._run_task.done():
            self._run_task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the client and close the connection."""
        self._stopping = True
        if self._run_task is not None:
            self._run_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._run_task
            self._run_task = None
        await self._close()

    async def _run(self) -> None:
        while not self._stopping:
            try:
                await self._connect_once()
                await self._read_loop()
            except (OSError, asyncio.TimeoutError) as err:
                _LOGGER.debug("AV8001 connection error: %s", err)
            finally:
                await self._close()
            if self._stopping:
                break
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _connect_once(self) -> None:
        _LOGGER.debug("Connecting to AV8001 gateway at %s:%s", self._host, self._port)
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self._host, self._port), timeout=CONNECT_TIMEOUT
        )
        _LOGGER.info("Connected to AV8001 gateway at %s:%s", self._host, self._port)
        if self._connection_callback:
            self._connection_callback(True)

    async def _read_loop(self) -> None:
        assert self._reader is not None
        buffer = b""
        while True:
            chunk = await self._reader.read(256)
            if not chunk:
                raise OSError("Connection closed by remote host")
            buffer += chunk
            while TERMINATOR.encode() in buffer:
                raw, buffer = buffer.split(TERMINATOR.encode(), 1)
                line = raw.decode("ascii", errors="ignore").strip()
                if line:
                    self._handle_line(line)

    def _handle_line(self, line: str) -> None:
        _LOGGER.debug("AV8001 <- %s", line)
        for prefix, future in list(self._pending.items()):
            if line.startswith(prefix) and not future.done():
                future.set_result(line)
                del self._pending[prefix]
        self._update_callback(line)

    async def _close(self) -> None:
        was_connected = self.connected
        if self._writer is not None:
            self._writer.close()
            with contextlib.suppress(OSError):
                await self._writer.wait_closed()
        self._reader = None
        self._writer = None
        for future in self._pending.values():
            if not future.done():
                future.cancel()
        self._pending.clear()
        if was_connected and self._connection_callback:
            self._connection_callback(False)

    async def async_send_command(self, command: str) -> None:
        """Send a fire-and-forget command."""
        if self._writer is None:
            raise AV8001Error("Not connected to AV8001 gateway")
        _LOGGER.debug("AV8001 -> %s", command)
        self._writer.write((command + TERMINATOR).encode("ascii"))
        await self._writer.drain()

    async def async_query(self, command: str, response_prefix: str) -> str | None:
        """Send a request command (e.g. 'PW?') and wait for the matching response."""
        if self._writer is None:
            raise AV8001Error("Not connected to AV8001 gateway")
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        self._pending[response_prefix] = future
        try:
            await self.async_send_command(command)
            return await asyncio.wait_for(future, timeout=COMMAND_TIMEOUT)
        except asyncio.TimeoutError:
            self._pending.pop(response_prefix, None)
            return None

