from enum import Enum
from typing import Any, Callable, Dict, Generic, Optional, TypeVar, Union

T = TypeVar("T")


class MerlinParameter(Generic[T]):
    def __init__(
        self,
        getter: Union[T, Callable[[], T]],
        setter: Optional[Callable[[T], None]] = None,
    ):
        self._value = getter
        self.set: Callable[[T], None] = (
            setter if setter is not None else self.default_set
        )

    def get(self) -> T:
        if callable(self._value):
            return self._value()
        return self._value

    def default_set(self, value: T):
        if callable(self._value):
            raise RuntimeError("Can not use default setter with custom getter")
        self._value = value


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


class GainMode(int, Enum):
    SLGM = 0
    LGM = 1
    HGM = 2
    SHGM = 3


class AcquisitionType(str, Enum):
    NORMAL = "Normal"
    TH_SCAN = "Th_scan"
    CONFIG = "Config"


class ChipMode(str, Enum):
    SPM = "SPM"
    CSM = "CSM"
    CM = "CM"
    CSCM = "CSCM"


class Trigger(int, Enum):
    POS = 0
    NEG = 1
    INT = 2


class Polarity(str, Enum):
    POS = "Positive"
    NEG = "Negative"


class State(int, Enum):
    IDLE = 0
    BUSY = 1
    Standby = 2


class ColourMode(int, Enum):
    MONOCHROME = 0
    COLOUR = 1


class GapFillMode(int, Enum):
    NONE = 0
    ZeroFill = 1
    Distribute = 2
    Interpolate = 3


class FileFormat(int, Enum):
    Binary = 0
    ASCII = 1


class TriggerOut(int, Enum):
    TriggerInTTL = 0
    TriggerInLVDS = 1
    TriggerInTTLDelayed = 2
    TriggerInLVDSDelayed = 3
    FollowShutter = 4
    OnePerAcqBurst = 5
    ShutterAndSensorReadout = 6
    Busy = 7


class CounterMode(int, Enum):
    Counter0 = 0
    Counter1 = 1
    Both = 2


# commands and default values
commands: Dict[CommandType, Dict[str, Any]] = {
    CommandType.CMD: {
        "STARTACQUISITION": None,
        "STOPACQUISITION": None,
        "SOFTTRIGGER": None,
        "THSCAN": None,
        "RESET": None,
        "ABORT": None,
    },
    CommandType.GET: {
        "SOFTWAREVERSION": "0.69.0.2",
        "TRIGGERINTTL": False,
        "TRIGGERINLVDS": False,
        "DETECTORSTATUS": State.IDLE,
        "TEMPERATURE": 0.0,
    },
    CommandType.SET: {
        "COLOURMODE": ColourMode.MONOCHROME,
        "CHARGESUMMING": False,
        "GAIN": GainMode.SLGM,
        "CONTINUOUSRW": False,
        "ENABLECOUNTER1": CounterMode.Counter0,
        "THRESHOLD0": 0.0,
        "THRESHOLD1": 0.0,
        "THRESHOLD2": 0.0,
        "THRESHOLD3": 0.0,
        "THRESHOLD4": 0.0,
        "THRESHOLD5": 0.0,
        "THRESHOLD6": 0.0,
        "THRESHOLD7": 0.0,
        "OPERATINGENERGY": 0.0,
        "COUNTERDEPTH": 12,
        "FILLMODE": GapFillMode.NONE,
        "FLATFIELDCORRECTION": False,
        "FLATFIELDFILE": "None",
        "MASKINDATA": False,
        "DEADTIMECORRECTION": False,
        "NUMFRAMESTOACQUIRE": 1,
        "ACQUISITIONTIME": 90.0,  # ms
        "ACQUISITIONPERIOD": 100.0,  # ms
        "TRIGGERSTART": Trigger.INT,
        "TRIGGERSTOP": Trigger.INT,
        "NUMFRAMESPERTRIGGER": 1,
        "TriggerOutTTL": TriggerOut.TriggerInTTL,
        "TriggerOutLVDS": TriggerOut.TriggerInTTL,
        "TriggerOutTTLInvert": False,
        "TriggerOutLVDSInvert": False,
        "TriggerInTTLDelay": 0,
        "TriggerInLVDSDelay": 0,
        "TriggerUseDelay": False,
        "SoftTriggerOutTTL": False,
        "SoftTriggerOutLVDS": False,
        "TriggerInTTL": False,
        "TriggerInLVDS": False,
        "THSCAN": 0,
        "THSTART": 0,
        "THSTOP": 0,
        "THSTEP": 0,
        "THNUMSTEPS": 0,
        "THWINDOWMODE": False,
        "THWINDOWSIZE": 0,
        "FILEDIRECTORY": "",
        "FILENAME": "",
        "FILEENABLE": False,
        "PIXELMATRIXLOADFILE": "",
        "FILECOUNTER": 0,
        "PIXELMATRIXSAVEFILE": "",
        "DACFILE": None,
        "FILEFORMAT": FileFormat.Binary,
        "POLARITY": Polarity.POS,
        "HVBIAS": 15,
    },
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
