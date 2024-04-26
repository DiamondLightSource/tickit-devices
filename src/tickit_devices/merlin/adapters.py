"""
We need an adapter with two sockets, one that receives and returns commands/responses
and one that spits out data

"""

import logging
from enum import Enum

from tickit.adapters.specifications.regex_command import RegexCommand
from tickit.adapters.tcp import CommandAdapter

from tickit_devices.merlin.commands import (
    DLIM,
    PREFIX,
    CommandType,
    ErrorCode,
    commands,
)
from tickit_devices.merlin.merlin import MerlinDetector, State
from tickit_devices.merlin.tcp import TcpPushAdapter

LOGGER = logging.getLogger("MerlinControlAdapter")


class MerlinDataAdapter(TcpPushAdapter):
    def __init__(self, detector: MerlinDetector):
        super().__init__()
        self.detector = detector

    def after_update(self) -> None:
        if self.detector.acquiring:
            message = self.detector.get_image()
            self.add_message_to_stream(message)


class MerlinControlAdapter(CommandAdapter):
    def __init__(self, detector: MerlinDetector, data_adapter: MerlinDataAdapter):
        self.detector = detector
        self.data_adapter = data_adapter

    # TODO
    def after_update(self) -> None: ...

    @RegexCommand(r"MPX,[0-9]{10},GET,([a-zA-Z0-9]*)$", format="utf-8")
    async def get(self, parameter: str) -> bytes:
        value = "0"
        code = ErrorCode.UNDERSTOOD
        if parameter not in commands[CommandType.GET] + commands[
            CommandType.SET
        ] or not hasattr(self.detector, parameter):
            code = ErrorCode.UNRECOGNISED
            LOGGER.error(f"Merlin does not have a parameter {parameter}")
        else:
            value = getattr(self.detector, parameter)
            if isinstance(value, bool):
                value = str(int(value))
            elif isinstance(value, Enum):
                value = str(value.value)
            elif isinstance(value, float):
                value = f"{value:.6f}"
            else:
                value = str(value)
        result_part = DLIM.join([CommandType.GET.value, parameter, value, code])
        response = DLIM.join([PREFIX, f"{(len(result_part) + 1):010}", result_part])
        print(response)
        return response.encode("utf-8")

    @RegexCommand(r"MPX,[0-9]{10},CMD,([a-zA-Z0-9]*)$", format="utf-8")
    async def cmd(self, command_name: str) -> bytes:
        command = getattr(self.detector, f"{command_name}_cmd", None)
        if command_name not in commands[CommandType.CMD] or command is None:
            LOGGER.error(f"Merlin does not have a command {command}")
            code = ErrorCode.UNRECOGNISED
        else:
            code = command()
        result_part = DLIM.join([CommandType.CMD.value, command_name, code])
        response = DLIM.join([PREFIX, f"{(len(result_part) + 1):010}", result_part])
        return response.encode("utf-8")

    @RegexCommand(r"MPX,[0-9]{10},SET,([a-zA-Z]*),([a-zA-Z0-9]*)$", format="utf-8")
    async def set(self, parameter: str, value: str) -> bytes:
        if parameter not in commands[CommandType.SET] or not hasattr(
            self.detector, parameter
        ):
            code = ErrorCode.UNRECOGNISED
            # TODO: is this the right error code for setting a read only value??
            LOGGER.error(f"Merlin can't set parameter {parameter}")
        elif self.detector.DETECTORSTATUS != State.IDLE:
            code = ErrorCode.BUSY
        else:
            code = self.detector.set_parameter(parameter, value)
        result_part = DLIM.join([CommandType.SET.value, parameter, code])
        response = DLIM.join([PREFIX, f"{(len(result_part) + 1):010}", result_part])
        return response.encode("utf-8")
