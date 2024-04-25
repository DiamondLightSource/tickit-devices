"""
We need an adapter with two sockets, one that receives and returns commands/responses
and one that spits out data

"""

from typing import Any, Tuple
import logging
from dataclasses import fields

from tickit_devices.merlin.commands import (
    parse_request,
    CommandType,
    request_command,
    ErrorCode,
    commands,
)
from tickit_devices.merlin.merlin import MerlinDetector, State
import asyncio
from tickit.adapters.tcp import CommandAdapter

LOGGER = logging.getLogger("MerlinControlAdapter")


class MerlinDataAdapter:
    def __init__(self, detector: MerlinDetector):
        self.detector = detector

    def after_update(self) -> None: ...


class MerlinControlAdapter(CommandAdapter):
    def __init__(self, detector: MerlinDetector, data_adapter: MerlinDataAdapter):
        self.detector = detector
        self.data_adapter = data_adapter

    def after_update(self) -> None: ...

    async def handle(self, message):
        response = parse_request(message, self)
        print(response, "now what do we do with this response")
        # this is where we accept commands, parsing should be done from here?

    def get(self, parameter: str) -> Tuple[Any, ErrorCode]:
        value = "0"
        code = ErrorCode.UNDERSTOOD
        if parameter not in commands[CommandType.GET] + commands[
            CommandType.SET
        ] or not hasattr(self.detector, parameter):
            code = ErrorCode.UNRECOGNISED
            LOGGER.error(f"Merlin does not have a parameter {parameter}")
        else:
            value = getattr(self.detector, parameter)
        return (value, code)

    def cmd(self, command: str) -> ErrorCode:
        code = ErrorCode.UNDERSTOOD
        if command not in commands[CommandType.CMD]:
            LOGGER.error(f"Merlin does not have a command {command}")
            code = ErrorCode.UNRECOGNISED
        else:
            ...  # add the rest of the command logic here
        return code

    def set(self, parameter: str, value: str) -> ErrorCode:
        code = ErrorCode.UNDERSTOOD
        if parameter not in commands[CommandType.GET] + commands[CommandType.SET]:
            code = ErrorCode.UNRECOGNISED
            LOGGER.error(f"Merlin does not have a parameter {parameter}")
        elif value == "bad":
            code = ErrorCode.RANGE
        elif self.detector.DETECTORSTATUS != State.IDLE:
            code = ErrorCode.BUSY
        return code


if __name__ in "__main__":
    merlin = MerlinDetector()
    data_adapter = MerlinDataAdapter(merlin)
    adapter = MerlinControlAdapter(merlin, data_adapter)
    print(request_command("GAIN", CommandType.GET))
    # print(merlin.get_acq_header().decode())
    # for command in commands[CommandType.SET]:
    #     print(parse_request(request_command(command, CommandType.GET), adapter))
