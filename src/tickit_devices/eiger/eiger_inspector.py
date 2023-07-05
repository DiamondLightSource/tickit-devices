import asyncio
import json
from pprint import pprint

import aiozmq
import zmq
from aiohttp import ClientResponse, ClientSession


async def zmq_listen(ready: asyncio.Event) -> None:
    addr = "tcp://127.0.0.1:9999"
    socket = await aiozmq.create_zmq_stream(zmq.PULL, connect=addr)
    try:
        print(f"Connected to {addr}")
        ready.set()
        while True:
            msg = await socket.read()
            print("Received new message:")
            formatted = json.loads(msg)
            pprint(formatted)
    finally:
        socket.close()


async def setup_eiger(session: ClientSession) -> None:
    print("Eiger setup")
    url_base = "http://localhost:8081/detector/api/1.8.0"
    async with session.put(f"{url_base}/command/initialize") as response:
        verify_sequence(response)

    print("Initialized")
    async with session.put(
        f"{url_base}/config/trigger_mode", json={"value": "ints"}
    ) as response:
        verify_sequence(response)
    print("Trigger mode set")
    async with session.put(f"{url_base}/command/arm") as response:
        verify_sequence(response)
    print("Armed")
    async with session.put(f"{url_base}/command/trigger") as resonse:
        verify_sequence(resonse)


def verify_sequence(response: ClientResponse) -> None:
    if response.status != 200:
        raise Exception(response.status)


async def main() -> None:
    ready = asyncio.Event()
    listen = asyncio.create_task(zmq_listen(ready))
    await ready.wait()
    async with ClientSession() as session:
        await setup_eiger(session)
    await listen


if __name__ == "__main__":
    asyncio.run(main())
