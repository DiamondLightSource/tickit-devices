from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import List, Tuple

from pydantic import BaseModel

from tickit_devices.merlin.acq_header import get_acq_header


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
            f"c:\\MERLIN_Quad_Config\\{self.id}\\{self.id}_{self.mode}.bpc"
            if self.enabled
            else ""
        )

    @property
    def dac_file(self):
        return (
            f"c:\\MERLIN_Quad_Config\\{self.id}\\{self.id}_{self.mode}.dacs"
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


class Merlin(BaseModel):
    counter_depth: int = 12
    chips: List[Chip] = [
        Chip(id="CHIP_1", x=0, y=0),
        Chip(id="CHIP_2", x=1, y=0, enabled=False),
        Chip(id="CHIP_3", x=0, y=1, enabled=False),
        Chip(id="CHIP_4", x=1, y=1, enabled=False),
    ]
    gap: bool = True  # 3px gap between chips
    colour_mode: bool = False
    _current_frame: int = 1
    _current_counter: int = 0
    shutter_time_ns: int = 10000000
    _configuration: str = ""
    gain_mode: GainMode = GainMode.SLGM
    _last_header: str = ""
    dead_time_file: str = "Dummy (C:\\<NUL>\\)"
    flat_field_file: str = "None"
    temperature: float = 0.0
    humidity: float = 0.0
    acq_type: AcquisitionType = AcquisitionType.NORMAL
    frames_in_acquisition: int = 1
    frames_per_trigger: int = 1
    trigger_start: Trigger = Trigger.INT
    trigger_stop: Trigger = Trigger.INT
    polarity: Polarity = Polarity.POS
    version: str = "0.69.0.2"
    voltage: int = 15
    counter_mode: int = 0  # 0, 1 or 2

    @property
    def shutter_time_s(self):
        return self.shutter_time_ns * 1e-9

    def get_resolution(self) -> Tuple[int, int]:
        chips = [c for c in self.chips if c.enabled]
        chip_size = 128 if self.colour_mode else 256
        x_gaps = max([c.x for c in chips]) - min(c.x for c in chips)
        y_gaps = max([c.y for c in chips]) - min(c.y for c in chips)
        # assuming in 2x2 configuration, TL, TR, BL, BR
        x = chip_size * (x_gaps + 1)
        y = chip_size * (y_gaps + 1)
        if self.gap:
            gap_size = 1 if self.colour_mode else 3
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

    def get_frame_header(self):
        enabled_chips = [c for c in self.chips if c.enabled]
        header_size = 256 + 128 * len(enabled_chips)
        x, y = self.get_resolution()
        pixels = x * y
        header_timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S.%f")
        chip_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f000Z")
        if self.counter_depth == 1:
            data_size = pixels // 8
            dtype = "U8"
        elif self.counter_depth == 6:
            data_size = pixels
            dtype = "U8"
        elif self.counter_depth == 12:
            data_size = pixels * 2
            dtype = "U16"
        elif self.counter_depth == 24:
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
                f"{self.shutter_time_s:.6f}",
                str(self._current_counter),
                str(int(self.colour_mode)),
                str(self.gain_mode.value),
            ]
        )
        header += "," + enabled_chips[0].get_threshold_string_scientific() + ",3RX,"
        for chip in enabled_chips:
            header += chip.get_dac_string() + ","
        header += "MQ1A,"
        header += f"{chip_timestamp},{self.shutter_time_ns}ns,{self.counter_depth},"
        self._last_header = header.ljust(header_size + 15, " ")
        # 15 is len("MPX,0000XXXXXX,")
        return self._last_header

    def get_acq_header(self):
        return get_acq_header(self)
