from functools import partial, reduce
from operator import and_, or_
from typing import Dict, TypedDict

import pydantic.v1.dataclasses
from tickit.core.components.device_simulation import DeviceSimulation
from tickit.core.device import DeviceUpdate
from tickit.core.typedefs import SimTime

from tickit_devices.zebra._common import Block, extract_bit, BlockConfig


class AndOrBlock(Block):
    """Represents an AND or OR gate"""

    class Inputs(TypedDict):
        INP1: bool
        INP2: bool
        INP3: bool
        INP4: bool

    class Outputs(TypedDict):
        OUT: bool

    def _get_input(self, inputs: Dict[str, bool], i: int) -> bool:
        enabled = extract_bit(self.params, f"{self.name}_ENA", i)
        inverted = extract_bit(self.params, f"{self.name}_INV", i)
        return enabled & inputs.get(f"INP{i + 1}", False) ^ inverted

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        op = and_ if self.name.startswith("AND") else or_
        get_input = partial(self._get_input, inputs)
        outputs = self.Outputs(OUT=reduce(op, map(get_input, range(4))))
        return DeviceUpdate(outputs, call_at=None)  # type: ignore


@pydantic.v1.dataclasses.dataclass
class AndOrBlockConfig(BlockConfig):

    def __call__(self) -> DeviceSimulation:
        return DeviceSimulation(name=self.name, device=AndOrBlock(name=self.name))
