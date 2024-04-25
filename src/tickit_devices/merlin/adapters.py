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
from tickit_devices.merlin.merlin import Merlin, State
import asyncio

LOGGER = logging.getLogger("MerlinAdapter")


class MerlinAdapter:
    def __init__(self, detector: Merlin):
        self.detector = detector

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
    merlin = Merlin()
    adapter = MerlinAdapter(merlin)
    print(merlin.get_acq_header().decode())
    for command in commands[CommandType.SET]:
        print(parse_request(request_command(command, CommandType.GET), adapter))