"""Connection lifecycle management for the Marantz AV8003 integration.

marantz_rs232's MarantzV2007Receiver is a connect-once client; it doesn't
retry on its own. This wraps it with a reconnect loop so a gateway reboot
or network blip doesn't require reloading the config entry.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging

from marantz_rs232 import MarantzV2007Receiver, V2007ReceiverState

from .const import CONNECT_TIMEOUT, MODEL, RECONNECT_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AV8003Connection:
    """Owns a MarantzV2007Receiver and keeps it connected."""

    def __init__(self, host: str, port: int) -> None:
        self.receiver = MarantzV2007Receiver(f"socket://{host}:{port}", model=MODEL)
        self._run_task: asyncio.Task | None = None
        self._stopping = False
        self._disconnected = asyncio.Event()
        self._disconnected.set()
        self.receiver.subscribe(self._on_state)

    @property
    def connected(self) -> bool:
        return self.receiver.connected

    def _on_state(self, state: V2007ReceiverState | None) -> None:
        if state is None:
            self._disconnected.set()

    def start(self) -> None:
        self._stopping = False
        if self._run_task is None or self._run_task.done():
            self._run_task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stopping = True
        if self._run_task is not None:
            self._run_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._run_task
            self._run_task = None
        await self.receiver.disconnect()

    async def _run(self) -> None:
        while not self._stopping:
            self._disconnected.clear()
            try:
                await asyncio.wait_for(self.receiver.connect(), timeout=CONNECT_TIMEOUT)
                await self.receiver.query_state()
            except (ConnectionError, OSError, asyncio.TimeoutError) as err:
                _LOGGER.debug("AV8003 connection attempt failed: %s", err)
                await asyncio.sleep(RECONNECT_INTERVAL)
                continue

            _LOGGER.info("Connected to AV8003")
            await self._disconnected.wait()
            _LOGGER.warning("Lost connection to AV8003, will retry")
            if self._stopping:
                break
            await asyncio.sleep(RECONNECT_INTERVAL)
