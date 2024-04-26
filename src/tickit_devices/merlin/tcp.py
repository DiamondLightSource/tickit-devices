import asyncio
from typing import Optional

from tickit.core.adapter import AdapterIo, RaiseInterrupt


class TcpPushAdapter:
    """An adapter interface for the ZeroMqPushIo."""

    _message_queue: Optional[asyncio.Queue]

    def __init__(self) -> None:
        self._message_queue = None

    def add_message_to_stream(self, message: bytes) -> None:
        self._ensure_queue().put_nowait(message)

    async def next_message(self) -> bytes:
        return await self._ensure_queue().get()

    def after_update(self) -> None: ...

    def _ensure_queue(self) -> asyncio.Queue:
        if self._message_queue is None:
            self._message_queue = asyncio.Queue()
        return self._message_queue


class TcpPushIo(AdapterIo["TcpPushAdapter"]):
    """AdapterIo for a ZeroMQ data stream."""

    _host: str
    _port: int
    _writer: Optional[asyncio.StreamWriter]
    _writer_lock: asyncio.Lock
    _task: Optional[asyncio.Task]

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5555,
    ) -> None:
        """Initialize with default values."""
        super().__init__()
        self._host = host
        self._port = port
        self._writer = None
        self._writer_lock = asyncio.Lock()
        self._task = None

    async def setup(
        self, adapter: TcpPushAdapter, raise_interrupt: RaiseInterrupt
    ) -> None:
        try:
            self.adapter = adapter
            server = await asyncio.start_server(
                self.send_messages_forever, self._host, self._port
            )
            self._task = asyncio.create_task(server.serve_forever())
        except asyncio.CancelledError:
            await self.shutdown()

    async def send_messages_forever(
        self, _: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        self._writer = writer
        while True:
            message = await self.adapter.next_message()
            await self.send_message(message)

    async def shutdown(self) -> None:
        if self._task:
            self._task.cancel()
        if self._writer is not None:
            self._writer.close()
            await self._writer.drain()

    async def send_message(self, message: bytes) -> None:
        if self._writer is not None:
            self._writer.write(message)
            await self._writer.drain()
