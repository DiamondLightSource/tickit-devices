import time
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple, Union

import numpy as np
import numpy.typing as npt
from tickit.core.device import Device, DeviceUpdate
from tickit.core.typedefs import SimTime
from typing_extensions import TypedDict

from tickit_devices.merlin.acq_header import get_acq_header
from tickit_devices.merlin.commands import ErrorCode, CommandType, commands


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


class Trigger(str, Enum):
    POS = "Positive"
    NEG = "Negative"
    INT = "Internal"


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
                f"{getattr(self.DACs, field.name):.7E}"
                for field in fields(self.DACs)
                if field.name.startswith("Threshold")
            ]
        )


@dataclass
class MerlinDetector(Device):
    COUNTERDEPTH: int = 12
    chips: List[Chip] = field(
        default_factory=lambda: [
            Chip(id="CHIP_1", x=0, y=0, enabled=True),
            Chip(id="CHIP_2", x=1, y=0, enabled=True),
            Chip(id="CHIP_3", x=0, y=1, enabled=True),
            Chip(id="CHIP_4", x=1, y=1, enabled=True),
        ]
    )
    gap: bool = True  # 3px gap between chips
    CONTINUOUSRW: bool = False
    _current_frame: int = 1
    _current_layer: int = 0
    shutter_time_ns: int = 10000000
    _configuration: str = ""
    acquiring: bool = False
    _images_remaining: int = 0
    GAIN: GainMode = GainMode.SLGM
    CHARGESUMMING: bool = False
    _last_header: str = ""
    chip_type: str = "Medipix 3RX"
    readout_system: str = "Merlin Quad"
    medipix_clock: int = 120
    dead_time_file: str = "Dummy (C:\\<NUL>\\)"
    FLATFIELDFILE: str = "None"
    FILLMODE: GapFillMode = GapFillMode.NONE
    TEMPERATURE: float = 0.0
    humidity: float = 0.0
    acq_type: AcquisitionType = AcquisitionType.NORMAL
    NUMFRAMESTOACQUIRE: int = 1
    NUMFRAMESPERTRIGGER: int = 1
    TRIGGERSTART: Trigger = Trigger.INT
    TRIGGERSTOP: Trigger = Trigger.INT
    POLARITY: Polarity = Polarity.POS
    SOFTWAREVERSION: str = "0.69.0.2"
    HVBIAS: int = 15
    ENABLECOUNTER1: CounterMode = CounterMode.Counter0
    DETECTORSTATUS: State = State.IDLE
    FILECOUNTER: int = 0
    FILEFORMAT: FileFormat = FileFormat.Binary
    FILEDIRECTORY: str = ""
    FILENAME: str = ""
    PIXELMATRIXSAVEFILE: str = ""
    PIXELMATRIXLOADFILE: str = ""
    FILEENABLE: bool = False
    TriggerOutTTL: TriggerOut = TriggerOut.TriggerInTTL
    TriggerOutLVDS: TriggerOut = TriggerOut.TriggerInTTL
    TriggerOutTTLInvert: bool = False
    TriggerOutLVDSInvert: bool = False
    TriggerInTTLDelay: int = 0
    TriggerInLVDSDelay: int = 0
    TriggerUseDelay: bool = False
    SoftTriggerOutTTL: bool = False
    SoftTriggerOutLVDS: bool = False
    TriggerInTTL: bool = False
    TriggerInLVDS: bool = False
    _last_image: Optional[npt.NDArray[Union[np.uint8, np.uint16, np.uint32]]] = None
    THSCAN: int = 0
    THSTART: float = 0
    THSTOP: float = 0
    THSTEP: float = 0
    THNUMSTEPS: int = 0
    OPERATINGENERGY: float = 0
    MASKINDATA: bool = False
    DEADTIMECORRECTION: bool = False
    THWINDOWMODE: bool = False
    THWINDOWSIZE: float = 0
    FLATFIELDCORRECTION: bool = False
    _gap_time_ns: int = 1000000
    _acq_header_enabled: bool = True
    _colour_mode: ColourMode = ColourMode.MONOCHROME

    @property
    def COLOURMODE(self) -> ColourMode:
        return self._colour_mode

    @COLOURMODE.setter
    def COLOURMODE(self, value: ColourMode):
        self._colour_mode = value
        if value:
            self.ENABLECOUNTER1 = CounterMode.Both

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
    def THRESHOLD0(self):
        print("Not doing correction calculation yet!!")
        return self.chips[0].DACs.Threshold0

    @property
    def THRESHOLD1(self):
        return self.chips[0].DACs.Threshold1

    @property
    def THRESHOLD2(self):
        return self.chips[0].DACs.Threshold2

    @property
    def THRESHOLD3(self):
        return self.chips[0].DACs.Threshold3

    @property
    def THRESHOLD4(self):
        return self.chips[0].DACs.Threshold4

    @property
    def THRESHOLD5(self):
        return self.chips[0].DACs.Threshold5

    @property
    def THRESHOLD6(self):
        return self.chips[0].DACs.Threshold6

    @property
    def THRESHOLD7(self):
        return self.chips[0].DACs.Threshold7

    @property
    def ACQUISITIONTIME(self):
        return self.shutter_time_ns * 1e-6

    @property
    def DACFILE(self):
        return self.chips[0].dac_file

    class Inputs(TypedDict, total=False):
        trigger: bool

    class Outputs(TypedDict): ...

    def set_parameter(self, parameter: str, value_str: str) -> ErrorCode:
        """Cast value to correct type and set"""
        try:
            attr = getattr(self, parameter)
            attr_type = type(attr)
            if isinstance(attr, Enum) and isinstance(attr, int):
                value = attr_type(int(value_str))
                setattr(self, parameter, attr_type(int(value)))
            else:
                value = attr_type(value_str)
            setattr(self, parameter, value)
            code = ErrorCode.UNDERSTOOD
        except Exception as e:  # TODO: use more specific exception
            print(e)
            code = ErrorCode.RANGE
        return code

    def STARTACQUISITION_cmd(self) -> ErrorCode:
        if self.DETECTORSTATUS is not State.IDLE:
            return ErrorCode.BUSY

        self.acquiring = True
        self._images_remaining = self.NUMFRAMESTOACQUIRE
        self._current_frame = 1
        # TODO: add NUMFRAMESPERTRIGGER logic, only really works with external triggers
        return ErrorCode.UNDERSTOOD

    def STOPACQUISITION_cmd(self) -> ErrorCode:
        self.DETECTORSTATUS = State.IDLE  # type: ignore
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
        # TODO: how does this work during acquisition?
        skip = ["chips"]
        for field in fields(self):
            if field.name in skip:
                continue
            setattr(self, field.name, field.default)
        return ErrorCode.UNDERSTOOD

    def ABORT_cmd(self) -> ErrorCode:
        # TODO: write command
        return ErrorCode.UNDERSTOOD

    def get_resolution(self) -> Tuple[int, int]:
        chips = [c for c in self.chips if c.enabled]
        chip_size = 128 if self.COLOURMODE == ColourMode.COLOUR else 256
        x_gaps = max([c.x for c in chips]) - min(c.x for c in chips)
        y_gaps = max([c.y for c in chips]) - min(c.y for c in chips)
        # assuming in 2x2 configuration, TL, TR, BL, BR
        x = chip_size * (x_gaps + 1)
        y = chip_size * (y_gaps + 1)
        if self.gap:
            gap_size = 1 if self.COLOURMODE == ColourMode.COLOUR else 3
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
        if self.COUNTERDEPTH == 1:
            data_size = pixels // 8
            dtype = "U8"
        elif self.COUNTERDEPTH == 6:
            data_size = pixels
            dtype = "U8"
        elif self.COUNTERDEPTH == 12:
            data_size = pixels * 2
            dtype = "U16"
        elif self.COUNTERDEPTH == 24:
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
                f"{len(enabled_chips):02}",  # double check if this is all chips or enabled chips
                f"{x:04}",
                f"{y:04}",
                dtype,
                self.get_configuration().rjust(6),
                self.get_chip_flags().rjust(2, "0"),
                header_timestamp,
                f"{self.ACQUISITIONTIME:.6f}",
                str(self._current_layer),
                str(int(self.COLOURMODE)),
                str(self.GAIN.value),
            ]
        )
        header += "," + enabled_chips[0].get_threshold_string_scientific() + ",3RX,"
        for chip in enabled_chips:
            header += chip.get_dac_string() + ","
        header += "MQ1A,"
        header += f"{chip_timestamp},{self.shutter_time_ns}ns,{self.COUNTERDEPTH},"
        self._last_header = header.ljust(header_size + 15, " ")
        # 15 is len("MPX,0000XXXXXX,")
        return self._last_header.encode("ascii")

    def get_acq_header(self) -> bytes:
        return get_acq_header(self).encode("ascii")

    def get_image(self):
        # TODO: handle two threshold and colour mode
        resolution = self.get_resolution()
        # we decrement until _current_layer reaches 0, append all the images together and send at once
        if self.ENABLECOUNTER1 == CounterMode.Both:
            layers = (
                list(range(8))
                if self.COLOURMODE == ColourMode.COLOUR
                else list(range(2))
            )
        elif self.ENABLECOUNTER1 == CounterMode.Counter0:
            layers = list(range(4)) if self.COLOURMODE == ColourMode.COLOUR else [0]
        else:  # self.ENABLECOUNTER1 == CounterMode.Counter1:
            layers = list(range(4, 8)) if self.COLOURMODE == ColourMode.COLOUR else [1]
        layers.reverse()
        if self._last_image is None or self._last_image.shape != resolution:
            # create new image, otherwise use existing one if same shape
            if self.COUNTERDEPTH == 1:
                raise NotImplementedError("1 bit images not currently supported")
            else:
                if self.COUNTERDEPTH == 6:
                    dtype = np.uint8
                elif self.COUNTERDEPTH == 12:
                    dtype = np.uint16
                else:  # 24 bit
                    dtype = np.uint32
                self._last_image = np.random.randint(  # type: ignore
                    2**self.COUNTERDEPTH, size=resolution, dtype=dtype
                )
                # create a black border for checking alignment of image
                self._last_image[:10, :] = 0
                self._last_image[-10:, :] = 0
                self._last_image[:, :10] = 0
                self._last_image[:, -10:] = 0
        if self._acq_header_enabled and self._current_frame == 1:
            message = self.get_acq_header()
        else:
            message = b""
        time.sleep(self.ACQUISITIONPERIOD * 1e-3)
        for layer in layers:
            self._current_layer = layer
            message += self.get_frame_header()
            message += self._last_image.tobytes()
        self._images_remaining -= 1
        self._current_frame += 1
        if self._images_remaining == 0:
            self.STOPACQUISITION_cmd()
        return message

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        # print('TODO: Doing nothing in update, see EigerDevice.update for comparison')
        return DeviceUpdate(self.Outputs(), SimTime(time))
