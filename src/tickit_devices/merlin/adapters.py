"""
We need an adapter with two sockets, one that receives and returns commands/responses
and one that spits out data

"""

from typing import Any
import logging

from tickit_devices.merlin.commands import (
    parse_request,
    CommandType,
    request_command,
    ErrorCode,
)
from tickit_devices.merlin.merlin import Merlin


class MerlinControlAdapter:
    def __init__(self, detector: Merlin): ...

    def get(self, parameter: str) -> Any:
        if parameter == "FAKE":
            raise KeyError(f"Merlin does not have a parameter {parameter}")
        # return dummy value for now
        return "1"

    def cmd(self, command: str) -> None:
        if command == "FAKE":
            raise KeyError(f"Merlin does not have a command {command}")

    def set(self, parameter: str, value: str) -> None:
        "either return nothing or raise an exception"
        if parameter == "FAKE":
            raise KeyError(f"Merlin does not have a parameter {parameter}")
        elif value == "bad":
            raise ValueError(f"{value} is not a valid value for {parameter}")


if __name__ in "__main__":
    merlin = Merlin()
    adapter = MerlinControlAdapter(merlin)
    print(
        parse_request(
            request_command("NUMFRAMESTOACQUIRE", CommandType.SET, 1), adapter
        )
    )
    print(
        parse_request(
            request_command("NUMFRAMESTOACQUIRE", CommandType.SET, "bad"), adapter
        )
    )
    print(parse_request(request_command("FAKE", CommandType.SET, "ok"), adapter))
    print(parse_request(request_command("GAIN", CommandType.SET, "bad"), adapter))
    # print(parse_request(request_command("DONOTHING", CommandType.CMD), adapter))
    print(request_command("DONOTHING", CommandType.CMD))
