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
        "SOFTWAREVERSION",
        "TRIGGERINTTL",
        "TRIGGERINLVDS",
        "DETECTORSTATUS",
        "TEMPERATURE",
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
        "TRIGGEROUTTTL",
        "TRIGGEROUTLVDS",
        "TRIGGEROUTTTLINVERT",
        "TRIGGEROUTLVDSINVERT",
        "TRIGGERINTTLDELAY",
        "TRIGGERINLVDSDELAY",
        "TRIGGERUSEDELAY",
        "SOFTTRIGGEROUTTTL",
        "SOFTTRIGGEROUTLVDS",
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
    parts = command.decode().split(DLIM)
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
    try:
        if command_type == CommandType.SET:
            if len(parts) != 5:
                return None
            adapter.set(parameter, parts[4])
        elif command_type == CommandType.GET:
            value = adapter.get(parameter)
        else:  # CMD
            adapter.cmd(parameter)
    except KeyError:
        code = ErrorCode.UNRECOGNISED
    except ValueError:
        code = ErrorCode.RANGE
    finally:
        parts = (
            [command_type.value, parameter, value, code]
            if command_type == CommandType.SET
            else [command_type.value, parameter, code]
        )
        response_part = DLIM.join([command_type.value, parameter, code])
    return DLIM.join(
        [PREFIX, f"{(len(response_part) + 1):010}", response_part]
    ).encode()
