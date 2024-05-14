from enum import Enum
from typing import Any


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
        "TriggerInTTLDelay",
        "TriggerInLVDSDelay",
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


def request_command(
    parameter: str, command_type: CommandType, value: Any = None
) -> bytes:
    if command_type == CommandType.SET:
        command_part = DLIM.join([command_type.value, parameter, str(value)])
    else:
        command_part = DLIM.join([command_type.value, parameter])
    command = DLIM.join([PREFIX, f"{(len(command_part) + 1):010}", command_part])
    return command.encode()
