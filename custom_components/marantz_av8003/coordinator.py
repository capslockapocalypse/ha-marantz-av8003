"""Connection lifecycle management for the Marantz AV8003 integration.

marantz_rs232's MarantzV2007Receiver is a connect-once client; it doesn't
retry on its own. This wraps it with a reconnect loop so a gateway reboot
or network blip doesn't require reloading the config entry.

The library only notices a dead link when the socket reports EOF or an error.
A gateway that drops off the network (power cut, Wi-Fi loss) leaves a
half-open TCP connection that never errors, so we also run a heartbeat and
force a reconnect when the receiver stops answering.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import contextlib
import logging

from marantz_rs232 import MarantzV2007Receiver, V2007ReceiverState

from .const import (
    CONNECT_TIMEOUT,
    HEARTBEAT_INTERVAL,
    HEARTBEAT_MAX_FAILURES,
    MODEL,
    RECONNECT_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

StateListener = Callable[[V2007ReceiverState | None], None]


class AV8003Connection:
    """Owns a MarantzV2007Receiver and keeps it connected."""

    def __init__(self, host: str, port: int) -> None:
        self.receiver = MarantzV2007Receiver(f"socket://{host}:{port}", model=MODEL)
        self._run_task: asyncio.Task | None = None
        self._stopping = False
        self._disconnected = asyncio.Event()
        self._disconnected.set()
        self._listeners: list[StateListener] = []
        self.receiver.subscribe(self._on_state)

    @property
    def connected(self) -> bool:
        return self.receiver.connected

    def subscribe(self, listener: StateListener) -> Callable[[], None]:
        """Register for state pushes, including (re)connect notifications."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def _broadcast(self, state: V2007ReceiverState | None) -> None:
        for listener in list(self._listeners):
            try:
                listener(state)
            except Exception:
                _LOGGER.exception("Error in AV8003 state listener %s", listener)

    def _on_state(self, state: V2007ReceiverState | None) -> None:
        if state is None:
            self._disconnected.set()
        self._broadcast(state)

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
            try:
                await self._connect_once()
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001 - must never kill the loop
                _LOGGER.debug("AV8003 connection attempt failed: %r", err)
                await self._safe_disconnect()
                await asyncio.sleep(RECONNECT_INTERVAL)
                continue

            _LOGGER.info("Connected to AV8003")
            # The library only notifies subscribers when a value *changes*, so
            # if the receiver's state is identical to before the drop nothing
            # would tell entities they're available again. Push it explicitly.
            self._broadcast(self.receiver.state)

            await self._monitor()
            if self._stopping:
                break
            _LOGGER.warning("Lost connection to AV8003, will retry")
            await self._safe_disconnect()
            await asyncio.sleep(RECONNECT_INTERVAL)

    async def _connect_once(self) -> None:
        self._disconnected.clear()
        await asyncio.wait_for(self.receiver.connect(), timeout=CONNECT_TIMEOUT)
        await self.receiver.query_state()
        if not self.receiver.connected:
            raise ConnectionError("Connection dropped during initial state query")

    async def _monitor(self) -> None:
        """Return once the link is down, either reported or detected by heartbeat."""
        failures = 0
        while not self._stopping:
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(
                    self._disconnected.wait(), timeout=HEARTBEAT_INTERVAL
                )
            if self._disconnected.is_set() or not self.receiver.connected:
                return
            try:
                await self.receiver.main.query_power()
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001
                failures += 1
                _LOGGER.debug(
                    "AV8003 heartbeat failed (%d/%d): %r",
                    failures,
                    HEARTBEAT_MAX_FAILURES,
                    err,
                )
                if failures >= HEARTBEAT_MAX_FAILURES:
                    _LOGGER.warning("AV8003 stopped responding to heartbeat")
                    return
            else:
                failures = 0

    async def _safe_disconnect(self) -> None:
        """Tear down whatever is left so the next connect() starts clean."""
        try:
            await self.receiver.disconnect()
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Error tearing down AV8003 connection", exc_info=True)
