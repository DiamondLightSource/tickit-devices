import time
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union

import numpy as np
from tickit.core.device import Device, DeviceUpdate
from tickit.core.typedefs import SimTime
from typing_extensions import TypedDict

from tickit_devices.merlin.acq_header import get_acq_header
from tickit_devices.merlin.parameters import (
    AcquisitionType,
    ChipMode,
    ColourMode,
    CommandType,
    CounterMode,
    ErrorCode,
    State,
    commands,
)

MAX_THRESHOLD = 100  # keV, assume that a DAC value of 2**9 - 1 represents this energy


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

    def set_threshold(self, threshold: int, value_keV: float):
        max_DAC = 2**9 - 1  # 511
        value_DAC = min(max_DAC, round(value_keV * max_DAC / MAX_THRESHOLD))
        setattr(self, f"Threshold{threshold}", value_DAC)

    def get_threshold_kev(self, threshold: int) -> float:
        value_DAC = getattr(self, f"Threshold{threshold}")
        max_DAC = 2**9 - 1  # 511
        return value_DAC * MAX_THRESHOLD / max_DAC


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
    _colour_mode: ColourMode = commands[CommandType.SET]["COLOURMODE"]
    _configuration: str = ""
    _detector_status: State = commands[CommandType.GET]["DETECTORSTATUS"]
    _images_remaining: int = 0
    _gap_time_ns: int = int(
        (
            commands[CommandType.SET]["ACQUISITIONPERIOD"]
            - commands[CommandType.SET]["ACQUISITIONTIME"]
        )
        * 1e6
    )
    _last_header: str = ""
    _last_encoded_image: Optional[bytes] = None
    _last_image_shape: Optional[Tuple[int, int]] = None
    _operating_energy: float = commands[CommandType.SET]["OPERATINGENERGY"]
    acq_type: AcquisitionType = AcquisitionType.NORMAL
    acquiring: bool = False
    chip_type: str = "Medipix 3RX"
    dead_time_file: str = "Dummy (C:\\<NUL>\\)"
    gap: bool = True  # 3px gap between chips
    humidity: float = 0.0
    medipix_clock: int = 120
    readout_system: str = "Merlin Quad"
    shutter_time_ns: int = int(commands[CommandType.SET]["ACQUISITIONTIME"] * 1e6)
    parameters: Dict[str, MerlinParameter[Any]] = field(default_factory=lambda: {})
    commands: Dict[str, Callable[[], ErrorCode]] = field(default_factory=lambda: {})

    def initialise(self):
        """Create parameters with custom getters/setters"""
        self.parameters["DETECTORSTATUS"] = MerlinParameter(
            lambda: self._detector_status,
            lambda val: setattr(self, "_detector_status", val),
        )
        self.parameters["THRESHOLD0"] = MerlinParameter(
            lambda: self.get_threshold(0),
            lambda val: self.set_threshold(0, val),
        )
        self.parameters["THRESHOLD1"] = MerlinParameter(
            lambda: self.get_threshold(1),
            lambda val: self.set_threshold(1, val),
        )
        self.parameters["THRESHOLD2"] = MerlinParameter(
            lambda: self.get_threshold(2),
            lambda val: self.set_threshold(2, val),
        )
        self.parameters["THRESHOLD3"] = MerlinParameter(
            lambda: self.get_threshold(3),
            lambda val: self.set_threshold(3, val),
        )
        self.parameters["THRESHOLD4"] = MerlinParameter(
            lambda: self.get_threshold(4),
            lambda val: self.set_threshold(4, val),
        )
        self.parameters["THRESHOLD5"] = MerlinParameter(
            lambda: self.get_threshold(5),
            lambda val: self.set_threshold(5, val),
        )
        self.parameters["THRESHOLD6"] = MerlinParameter(
            lambda: self.get_threshold(6),
            lambda val: self.set_threshold(6, val),
        )
        self.parameters["THRESHOLD7"] = MerlinParameter(
            lambda: self.get_threshold(7),
            lambda val: self.set_threshold(7, val),
        )
        self.parameters["COLOURMODE"] = MerlinParameter(
            lambda: self._colour_mode, lambda val: self.set_colour_mode(val)
        )
        self.parameters["DACFILE"] = MerlinParameter(
            lambda: self.chips[0].dac_file,
            lambda val: setattr(self.chips[0], "dac_file", val),
        )
        self.parameters["ACQUISITIONTIME"] = MerlinParameter(
            lambda: self.shutter_time_ns * 1e-6,  # returns in ms
            lambda val: self.set_acq_time(val),
        )
        self.parameters["ACQUISITIONPERIOD"] = MerlinParameter(
            lambda: (self._gap_time_ns + self.shutter_time_ns) * 1e-6,
            lambda val: self.set_acq_period(val),
        )
        self.parameters["OPERATINGENERGY"] = MerlinParameter(
            lambda: self._operating_energy,
            lambda val: self.set_operating_energy(val),
        )
        ro_params: Dict[str, MerlinParameter[Any]] = {
            parameter: MerlinParameter(default_value)
            for parameter, default_value in commands[CommandType.GET].items()
            if parameter not in self.parameters
        }
        self.parameters.update(ro_params)
        rw_params: Dict[str, MerlinParameter[Any]] = {
            parameter: MerlinParameter(default_value)
            for parameter, default_value in commands[CommandType.SET].items()
            if parameter not in self.parameters
        }
        self.parameters.update(rw_params)
        self.commands.update({"STARTACQUISITION": self.start_acquisition_cmd,
                              "STOPACQUISITION": self.stop_acquisition_cmd,
                              "SOFTTRIGGER": self.soft_trigger_cmd,
                              "THSCAN": self.threshold_scan_cmd,
                              "RESET": self.reset_cmd,
                              "ABORT": self.abort_cmd})

    def get(self, parameter: str):
        return self.parameters[parameter].get()

    def set_operating_energy(self, value: float):
        self._operating_energy = value
        half_value = value / 2
        for threshold in range(8):
            self.set_threshold(threshold, half_value)

    def get_threshold(self, threshold: int):
        return self.chips[0].DACs.get_threshold_kev(threshold)

    def set_threshold(self, threshold: int, value: float):
        if value < 0:
            raise ValueError("Threshold energy should be positive")
        for chip in self.chips:
            chip.DACs.set_threshold(threshold, value)

    def set_colour_mode(self, colour_mode: ColourMode):
        self._colour_mode = colour_mode
        if self.get("COLOURMODE") == ColourMode.COLOUR:
            self.set_param("ENABLECOUNTER1", CounterMode.Both)

    def set_acq_time(self, value: float):
        new_shutter_time_ns = int(1e6 * value)
        # adjust gap time so that acq period doesn't change
        self._gap_time_ns += self.shutter_time_ns - new_shutter_time_ns
        self.shutter_time_ns = new_shutter_time_ns

    def set_acq_period(self, value: float):
        # value comes in in ms
        value_ns = 1e6 * value
        if value_ns >= self.shutter_time_ns:
            # enforce minimum readout time of 822us
            self._gap_time_ns = int(max(value_ns - self.shutter_time_ns, 822e3))
        else:
            # TODO: double check if this returns a RANGE error or not.
            raise ValueError("Can not set acquisition period below shutter period")

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

    def start_acquisition_cmd(self) -> ErrorCode:
        if self.get("DETECTORSTATUS") is not State.IDLE:
            return ErrorCode.BUSY

        self.acquiring = True
        self._images_remaining = self.get("NUMFRAMESTOACQUIRE")
        self._current_frame = 1
        # TODO: add NUMFRAMESPERTRIGGER logic, only really works with external triggers
        return ErrorCode.UNDERSTOOD

    def stop_acquisition_cmd(self) -> ErrorCode:
        self.set_param("DETECTORSTATUS", State.IDLE)
        self.acquiring = False
        self._current_frame = 1
        self._current_layer = 0
        return ErrorCode.UNDERSTOOD

    def soft_trigger_cmd(self) -> ErrorCode:
        # TODO: write command
        return ErrorCode.UNDERSTOOD

    def threshold_scan_cmd(self) -> ErrorCode:
        # TODO: write command
        return ErrorCode.UNDERSTOOD

    def reset_cmd(self) -> ErrorCode:
        for ctype in [CommandType.GET, CommandType.SET]:
            for parameter, default in commands[ctype].items():
                try:
                    if default is not None:
                        self.set_param(parameter, default)
                    else:
                        print("No default value set for", parameter)
                except RuntimeError:
                    print("Could not reset parameter", parameter)
        return ErrorCode.UNDERSTOOD

    def abort_cmd(self) -> ErrorCode:
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
            self.stop_acquisition_cmd()
        return message

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        return DeviceUpdate(self.Outputs(), SimTime(time))
