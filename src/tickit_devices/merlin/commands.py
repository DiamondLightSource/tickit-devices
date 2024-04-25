from enum import Enum
from typing import Any
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tickit_devices.merlin.adapters import MerlinControlAdapter


class CommandType(str, Enum):
    CMD = "CMD"
    SET = "SET"
    GET = "GET"


class ErrorCode(str, Enum):
    UNDERSTOOD = "0"
    BUSY = "1"
    UNRECOGNISED = "2"
    RANGE = "3"


DLIM = ","
PREFIX = "MPX"

commands = {
    CommandType.CMD: [
        "STARTACQUISITION",
        "STOPACQUISITION",
        "SOFTTRIGGER",
        "THSCAN",
        "RESET",
        "ABORT",
    ],
    CommandType.GET: [
        "SOFTWAREVERSION",
        "TRIGGERINTTL",
        "TRIGGERINLVDS",
        "DETECTORSTATUS",
        "TEMPERATURE",
    ],
    CommandType.SET: [
        "COLOURMODE",
        "CHARGESUMMING",
        "GAIN",
        "CONTINUOUSRW",
        "ENABLECOUNTER1",
        "THRESHOLD0",
        "THRESHOLD1",
        "THRESHOLD2",
        "THRESHOLD3",
        "THRESHOLD4",
        "THRESHOLD5",
        "THRESHOLD6",
        "THRESHOLD7",
        "OPERATINGENERGY",
        "COUNTERDEPTH",
        "FILLMODE",
        "FLATFIELDCORRECTION",
        "FLATFIELDFILE",
        "MASKINDATA",
        "DEADTIMECORRECTION",
        "NUMFRAMESTOACQUIRE",
        "ACQUISITIONTIME",
        "ACQUISITIONPERIOD",
        "TRIGGERSTART",
        "TRIGGERSTOP",
        "NUMFRAMESPERTRIGGER",
        "TriggerOutTTL",
        "TriggerOutLVDS",
        "TriggerOutTTLInvert",
        "TriggerOutLVDSInvert",
        "TriggerOutTTLDelay",
        "TriggerOutLVDSDelay",
        "TriggerUseDelay",
        "SoftTriggerOutTTL",
        "SoftTriggerOutLVDS",
        "TriggerInTTL",
        "TriggerInLVDS",
        "THSCAN",
        "THSTART",
        "THSTOP",
        "THSTEP",
        "THNUMSTEPS",
        "THWINDOWMODE",
        "THWINDOWSIZE",
        "FILEDIRECTORY",
        "FILENAME",
        "FILEENABLE",
        "PIXELMATRIXLOADFILE",
        "FILECOUNTER",
        "PIXELMATRIXSAVEFILE",
        "DACFILE",
        "FILEFORMAT",
        "POLARITY",
        "HVBIAS",
    ],
}


# we don't need this
def request_command(
    parameter: str, command_type: CommandType, value: Any = None
) -> bytes:
    if command_type == CommandType.SET:
        command_part = DLIM.join([command_type.value, parameter, str(value)])
    else:
        command_part = DLIM.join([command_type.value, parameter])
    command = DLIM.join([PREFIX, f"{(len(command_part) + 1):010}", command_part])
    return command.encode()


def parse_request(command: bytes, adapter: "MerlinControlAdapter") -> bytes | None:
    """
    Read encoded command and return encoded response
    """
    parts = command.decode().rstrip("\r\n").split(DLIM)
    if (
        parts[0] != PREFIX
        or not re.match(r"^[0-9]{10}$", parts[1])
        or parts[2] not in CommandType.__members__
    ):
        return None  # to indicate that message would not be read
    command_type = CommandType(parts[2])
    parameter = parts[3]
    code = ErrorCode.UNDERSTOOD
    value = "0"  # default in case get fails
    if command_type == CommandType.SET:
        if len(parts) != 5:
            return None
        code = adapter.set(parameter, parts[4])
    elif command_type == CommandType.GET:
        value, code = adapter.get(parameter)
        if isinstance(value, bool):
            value = str(int(value))
        elif isinstance(value, Enum):
            value = str(value.value)
        elif isinstance(value, float):
            value = f"{value:.6f}"
        else:
            value = str(value)
    else:  # CMD
        code = adapter.cmd(parameter)
    parts = (
        [command_type.value, parameter, value, code]
        if command_type == CommandType.GET
        else [command_type.value, parameter, code]
    )
    response_part = DLIM.join(parts)
    return DLIM.join(
        [PREFIX, f"{(len(response_part) + 1):010}", response_part]
    ).encode()
