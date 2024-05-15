import time
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from tickit.core.device import Device, DeviceUpdate
from tickit.core.typedefs import SimTime
from typing_extensions import TypedDict

from tickit_devices.merlin.acq_header import get_acq_header
from tickit_devices.merlin.commands import ErrorCode

from typing import Generic, TypeVar


@dataclass
class ChipDACs:
    Threshold0: int = field(default=0)
    Threshold1: int = field(default=0)
    Threshold2: int = field(default=0)
    Threshold3: int = field(default=0)
    Threshold4: int = field(default=0)
    Threshold5: int = field(default=0)
    Threshold6: int = field(default=0)
    Threshold7: int = field(default=0)
    Preamp: int = field(default=175)
    Ikrum: int = field(default=10)
    Shaper: int = field(default=200)
    Disc: int = field(default=128)
    Disc_LS: int = field(default=100)
    ShaperTest: int = field(default=0)
    DACDiscL: int = field(default=100)
    Delay: int = field(default=30)
    TPBufferIn: int = field(default=128)
    TPBufferOut: int = field(default=4)
    RPZ: int = field(default=255)
    GND: int = field(default=105)
    TPRef: int = field(default=128)
    FBK: int = field(default=156)
    Cas: int = field(default=144)
    TPRefA: int = field(default=511)
    TPRefB: int = field(default=511)


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


@dataclass
class Chip:
    id: str
    DACs: ChipDACs = ChipDACs()
    enabled: bool = True
    x: int = 0
    y: int = 0  # arrangement of chips
    mode: ChipMode = ChipMode.SPM

    def get_id_for_header(self):
        return self.id if self.enabled else "- "

    @property
    def bpc_file(self):
        return (
            rf"c:\MERLIN_Quad_Config\{self.id}\{self.id}_{self.mode}.bpc"
            if self.enabled
            else ""
        )

    @property
    def dac_file(self):
        return (
            rf"c:\MERLIN_Quad_Config\{self.id}\{self.id}_{self.mode}.dacs"
            if self.enabled
            else ""
        )

    def get_dac_string(self):
        return ",".join(
            [f"{getattr(self.DACs, field.name):03}" for field in fields(self.DACs)]
        )

    def get_threshold_string_scientific(self):
        return ",".join(
            [
                f"{getattr(self.DACs, f.name):.7E}"
                for f in fields(self.DACs)
                if f.name.startswith("Threshold")
            ]
        )


T = TypeVar("T")


# TODO: maybe TypeVar is inappropriate here
class MerlinParameter(Generic[T]):
    _value: Optional[T]

    def __init__(
        self,
        value: Optional[T] = None,
        getter: Optional[Callable[[], T]] = None,
        setter: Optional[Callable[[T], None]] = None,
    ):
        self._value = value
        self.get: Callable[[], T] = getter if getter is not None else self.default_get
        self.set: Callable[[T], None] = setter if setter is not None else self.default_set

    def default_get(self) -> T:
        return self._value

    # TODO: test this!!
    def default_set(self, value: T):
        self._value = value


@dataclass
class MerlinDetector(Device):
    chips: List[Chip] = field(
        default_factory=lambda: [
            Chip(id="CHIP_1", x=0, y=0, enabled=True),
            Chip(id="CHIP_2", x=1, y=0, enabled=True),
            Chip(id="CHIP_3", x=0, y=1, enabled=True),
            Chip(id="CHIP_4", x=1, y=1, enabled=True),
        ]
    )
    _acq_header_enabled: bool = True
    _current_frame: int = 1
    _current_layer: int = 0
    _colour_mode: ColourMode = ColourMode.MONOCHROME
    _configuration: str = ""
    _images_remaining: int = 0
    _gap_time_ns: int = 1000000
    _last_header: str = ""
    _last_encoded_image: Optional[bytes] = None
    _last_image_shape: Optional[Tuple[int, int]] = None
    acq_type: AcquisitionType = AcquisitionType.NORMAL
    acquiring: bool = False
    chip_type: str = "Medipix 3RX"
    dead_time_file: str = "Dummy (C:\\<NUL>\\)"
    gap: bool = True  # 3px gap between chips
    humidity: float = 0.0
    medipix_clock: int = 120
    readout_system: str = "Merlin Quad"
    shutter_time_ns: int = 10000000
    parameters: Dict[str, MerlinParameter[Any]] = field(
        default_factory=lambda: {
            "COUNTERDEPTH": MerlinParameter(12),
            "CHARGESUMMING": MerlinParameter(False),
            "CONTINUOUSRW": MerlinParameter(False),
            "DEADTIMECORRECTION": MerlinParameter(False),
            "DETECTORSTATUS": MerlinParameter(State.IDLE),
            "ENABLECOUNTER1": MerlinParameter(CounterMode.Counter0),
            "FILECOUNTER": MerlinParameter(0),
            "FILEDIRECTORY": MerlinParameter(""),
            "FILEENABLE": MerlinParameter(False),
            "FILEFORMAT": MerlinParameter(FileFormat.Binary),
            "FILLMODE": MerlinParameter(GapFillMode.NONE),
            "FILENAME": MerlinParameter(""),
            "FLATFIELDCORRECTION": MerlinParameter(False),
            "FLATFIELDFILE": MerlinParameter("None"),
            "GAIN": MerlinParameter(GainMode.SLGM),
            "HVBIAS": MerlinParameter(15),
            "MASKINDATA": MerlinParameter(False),
            "NUMFRAMESTOACQUIRE": MerlinParameter(1),
            "NUMFRAMESPERTRIGGER": MerlinParameter(1),
            "OPERATINGENERGY": MerlinParameter(0),
            "PIXELMATRIXSAVEFILE": MerlinParameter(""),
            "PIXELMATRIXLOADFILE": MerlinParameter(""),
            "POLARITY": MerlinParameter(Polarity.POS),
            "SOFTWAREVERSION": MerlinParameter("0.69.0.2"),
            "TEMPERATURE": MerlinParameter(0.0),
            "THNUMSTEPS": MerlinParameter(0),
            "THSTART": MerlinParameter(0),
            "THSTEP": MerlinParameter(0),
            "THSCAN": MerlinParameter(0),
            "THSTOP": MerlinParameter(0),
            "THWINDOWMODE": MerlinParameter(False),
            "THWINDOWSIZE": MerlinParameter(0),
            "TRIGGERSTART": MerlinParameter(Trigger.INT),
            "TRIGGERSTOP": MerlinParameter(Trigger.INT),
            "SoftTriggerOutTTL": MerlinParameter(False),
            "SoftTriggerOutLVDS": MerlinParameter(False),
            "TriggerInTTLDelay": MerlinParameter(0),
            "TriggerInLVDSDelay": MerlinParameter(0),
            "TriggerOutTTL": MerlinParameter(TriggerOut.TriggerInTTL),
            "TriggerOutLVDS": MerlinParameter(TriggerOut.TriggerInTTL),
            "TriggerOutTTLInvert": MerlinParameter(False),
            "TriggerOutLVDSInvert": MerlinParameter(False),
            "TriggerUseDelay": MerlinParameter(False),
            "TriggerInTTL": MerlinParameter(False),
            "TriggerInLVDS": MerlinParameter(False),
        }
    )

    def initialise(self):
        """Create parameters with custom getters/setters"""
        self.parameters["THRESHOLD0"] = MerlinParameter(
            None,
            lambda: self.chips[0].DACs.Threshold0,
            lambda val: self.set_threshold(0, val),
        )
        self.parameters["THRESHOLD1"] = MerlinParameter(
            None,
            lambda: self.chips[0].DACs.Threshold1,
            lambda val: self.set_threshold(1, val),
        )
        self.parameters["THRESHOLD2"] = MerlinParameter(
            None,
            lambda: self.chips[0].DACs.Threshold2,
            lambda val: self.set_threshold(2, val),
        )
        self.parameters["THRESHOLD3"] = MerlinParameter(
            None,
            lambda: self.chips[0].DACs.Threshold3,
            lambda val: self.set_threshold(3, val),
        )
        self.parameters["THRESHOLD4"] = MerlinParameter(
            None,
            lambda: self.chips[0].DACs.Threshold4,
            lambda val: self.set_threshold(4, val),
        )
        self.parameters["THRESHOLD5"] = MerlinParameter(
            None,
            lambda: self.chips[0].DACs.Threshold5,
            lambda val: self.set_threshold(5, val),
        )
        self.parameters["THRESHOLD6"] = MerlinParameter(
            None,
            lambda: self.chips[0].DACs.Threshold6,
            lambda val: self.set_threshold(6, val),
        )
        self.parameters["THRESHOLD7"] = MerlinParameter(
            None,
            lambda: self.chips[0].DACs.Threshold7,
            lambda val: self.set_threshold(7, val),
        )
        self.parameters["COLOURMODE"] = MerlinParameter(
            None,
            lambda: self._colour_mode,
            lambda val: self.set_colour_mode(val)
        )
        self.parameters["DACFILE"] = MerlinParameter(
            None,
            lambda: self.chips[0].dac_file,
            lambda val: setattr(self.chips[0], "dac_file", val)
        )

    def get(self, parameter: str):
        return self.parameters[parameter].get()

    def set_threshold(self, threshold: int, value_str: int):
        setattr(self.chips[0].DACs, f"Threshold{threshold}", int(value_str))

    def set_colour_mode(self, value_str: str):
        self.parameters["COLOURMODE"].default_set(value_str)
        if self.get("COLOURMODE") == ColourMode.COLOUR:
            self.set_param("ENABLECOUNTER1", CounterMode.Both)

    @property
    def ACQUISITIONPERIOD(self) -> float:
        # returns as ms
        return (self._gap_time_ns + self.shutter_time_ns) * 1e-6

    @ACQUISITIONPERIOD.setter
    def ACQUISITIONPERIOD(self, value: float):
        # value comes in in ms
        value_ns = 1e6 * value
        if value_ns >= self.shutter_time_ns:
            # enforce minimum readout time of 822us
            self._gap_time_ns = int(max(value_ns - self.shutter_time_ns, 822e3))
        else:
            # TODO: double check if this returns a RANGE error or not.
            raise ValueError("Can not set acquisition period below shutter period")

    @property
    def ACQUISITIONTIME(self):
        return self.shutter_time_ns * 1e-6

    class Inputs(TypedDict, total=False):
        trigger: bool

    class Outputs(TypedDict): ...

    def set_param(self, parameter: str, value: Any):
        self.parameters[parameter].set(value)

    def set_param_from_string(self, parameter: str, value_str: str) -> ErrorCode:
        """Cast value to correct type and set"""
        try:
            attr = self.get(parameter)  # get current value to determine type
            # we could probably pass the type to MerlinParameter instead
            attr_type = type(attr)
            if isinstance(attr, Enum) and isinstance(attr, int):
                value = attr_type(int(value_str))
            else:
                value = attr_type(value_str)
            self.set_param(parameter, value)
            code = ErrorCode.UNDERSTOOD
        except Exception as e:  # TODO: use more specific exception
            print(e)
            code = ErrorCode.RANGE
        return code

    def STARTACQUISITION_cmd(self) -> ErrorCode:
        if self.get("DETECTORSTATUS") is not State.IDLE:
            return ErrorCode.BUSY

        self.acquiring = True
        self._images_remaining = self.get("NUMFRAMESTOACQUIRE")
        self._current_frame = 1
        # TODO: add NUMFRAMESPERTRIGGER logic, only really works with external triggers
        return ErrorCode.UNDERSTOOD

    def STOPACQUISITION_cmd(self) -> ErrorCode:
        self.set_param("DETECTORSTATUS", State.IDLE)
        self.acquiring = False
        self._current_frame = 1
        self._current_layer = 0
        return ErrorCode.UNDERSTOOD

    def SOFTTRIGGER_cmd(self) -> ErrorCode:
        # TODO: write command
        return ErrorCode.UNDERSTOOD

    def THSCAN_cmd(self) -> ErrorCode:
        # TODO: write command
        return ErrorCode.UNDERSTOOD

    def RESET_cmd(self) -> ErrorCode:
        raise NotImplementedError("Fix this")
        # TODO: how does this work during acquisition?
        # skip = ["chips"]
        # for f in fields(self):
        #     if f.name in skip:
        #         continue
        #     setattr(self, f.name, f.default)
        # return ErrorCode.UNDERSTOOD

    def ABORT_cmd(self) -> ErrorCode:
        # TODO: write command
        return ErrorCode.UNDERSTOOD

    def get_resolution(self) -> Tuple[int, int]:
        chips = [c for c in self.chips if c.enabled]
        colour_mode = self.get("COLOURMODE")
        chip_size = 128 if colour_mode == ColourMode.COLOUR else 256
        x_gaps = max([c.x for c in chips]) - min(c.x for c in chips)
        y_gaps = max([c.y for c in chips]) - min(c.y for c in chips)
        # assuming in 2x2 configuration, TL, TR, BL, BR
        x = chip_size * (x_gaps + 1)
        y = chip_size * (y_gaps + 1)
        if self.gap:
            gap_size = 1 if colour_mode == ColourMode.COLOUR else 3
            x += x_gaps * gap_size
            y += y_gaps * gap_size
        return (x, y)

    def get_configuration(self):
        if not self._configuration:
            x_chips = max([c.x for c in self.chips]) - min(c.x for c in self.chips) + 1
            y_chips = max([c.y for c in self.chips]) - min(c.y for c in self.chips) + 1
            config = f"{x_chips}x{y_chips}"
            if self.gap:
                config += "G"
            self._configuration = config
        return self._configuration

    def get_chip_flags(self) -> str:
        bits = 0
        for idx, chip in enumerate(self.chips):
            if chip.enabled:
                bits += 2**idx
        return hex(bits)[2:]  # discard hex prefix

    def get_frame_header(self) -> bytes:
        enabled_chips = [c for c in self.chips if c.enabled]
        header_size = 256 + 128 * len(enabled_chips)
        x, y = self.get_resolution()
        pixels = x * y
        header_timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S.%f")
        chip_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f000Z")
        depth = self.get("COUNTERDEPTH")
        if depth == 1:
            data_size = pixels // 8
            dtype = "U8"
        elif depth == 6:
            data_size = pixels
            dtype = "U8"
        elif depth == 12:
            data_size = pixels * 2
            dtype = "U16"
        elif depth == 24:
            data_size = pixels * 4
            dtype = "U32"
        else:
            raise ValueError(
                "Could not calculate image size from invalid counter depth"
            )
        header = ",".join(
            [
                "MPX",
                f"{(header_size + data_size + 1):010}",
                "MQ1",
                f"{self._current_frame:06}",
                f"{header_size:05}",
                f"{len(enabled_chips):02}",
                f"{x:04}",
                f"{y:04}",
                dtype,
                self.get_configuration().rjust(6),
                self.get_chip_flags().rjust(2, "0"),
                header_timestamp,
                f"{self.get('ACQUISITIONTIME'):.6f}",
                str(self._current_layer),
                str(int(self.get("COLOURMODE"))),
                str(self.get("GAIN").value),
            ]
        )
        header += "," + enabled_chips[0].get_threshold_string_scientific() + ",3RX,"
        for chip in enabled_chips:
            header += chip.get_dac_string() + ","
        header += "MQ1A,"
        header += (
            f"{chip_timestamp},{self.shutter_time_ns}ns,{self.get('COUNTERDEPTH')},"
        )
        self._last_header = header.ljust(header_size + 15, " ")
        # 15 is len("MPX,0000XXXXXX,")
        return self._last_header.encode("ascii")

    def get_acq_header(self) -> bytes:
        return get_acq_header(self).encode("ascii")

    def get_image(self):
        # TODO: handle two threshold and colour mode
        resolution = self.get_resolution()
        colour_mode = self.get("COLOURMODE")
        counter_mode = self.get("ENABLECOUNTER1")
        if counter_mode == CounterMode.Both:
            layers = (
                list(range(8)) if colour_mode == ColourMode.COLOUR else list(range(2))
            )
        elif counter_mode == CounterMode.Counter0:
            layers = list(range(4)) if colour_mode == ColourMode.COLOUR else [0]
        else:  # counter_mode == CounterMode.Counter1:
            layers = list(range(4, 8)) if colour_mode == ColourMode.COLOUR else [1]
        layers.reverse()
        if self._last_encoded_image is None or self._last_image_shape != resolution:
            # create new image, otherwise use existing one if same shape
            depth = self.get("COUNTERDEPTH")
            if depth == 1:
                image = b""
                pixels = resolution[0] * resolution[1]
                for _ in range(pixels // 8):
                    # generate random bytes
                    image += bytes([np.random.randint(2)])
                # if there is a remainder of pixels that doesn't divide into 8
                # add a zeroed byte to the end.
                if pixels % 8:
                    image += bytes([0])
                self._last_encoded_image = image
            else:
                if depth == 6:
                    dtype = np.uint8
                elif depth == 12:
                    dtype = np.uint16
                else:  # 24 bit
                    dtype = np.uint32
                image = np.random.randint(  # type: ignore
                    2**depth, size=resolution, dtype=dtype
                )
                # create a black border for checking alignment of image
                image[:10, :] = 0
                image[-10:, :] = 0
                image[:, :10] = 0
                image[:, -10:] = 0
                self._last_encoded_image = image.tobytes()
            self._last_image_shape = resolution
        if self._acq_header_enabled and self._current_frame == 1:
            message = self.get_acq_header()
        else:
            message = b""
        time.sleep(self.get("ACQUISITIONPERIOD") * 1e-3)
        # decrement until _current_layer reaches 0
        # append all the images together and send at once
        for layer in layers:
            self._current_layer = layer
            message += self.get_frame_header()
            message += self._last_encoded_image
        self._images_remaining -= 1
        self._current_frame += 1
        if self._images_remaining == 0:
            self.STOPACQUISITION_cmd()
        return message

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        # print('TODO: Doing nothing in update, see EigerDevice.update for comparison')
        return DeviceUpdate(self.Outputs(), SimTime(time))
