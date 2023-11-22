from functools import partial, reduce
from operator import and_, or_
from typing import Dict, TypedDict

import pydantic.v1.dataclasses
from tickit.core.components.device_component import DeviceComponent

from tickit_devices.zebra._common import Block, BlockConfig, extract_bit


class AndOrBlock(Block):
    """
    Represents an AND or OR gate with 4 inputs.
    If an input is not enabled, it will always be considered False,
    unless it is also inverted.
    """

    class Inputs(TypedDict):
        INP1: bool
        INP2: bool
        INP3: bool
        INP4: bool

    class Outputs(TypedDict):
        OUT: bool

    def __init__(self, name: str):
        super().__init__(name=name, previous_outputs=self.Outputs(OUT=False))

    def _get_input(self, inputs: Dict[str, bool], i: int) -> bool:
        if not self.params:
            raise ValueError
        enabled = extract_bit(self.params, f"{self.name}_ENA", i)
        inverted = extract_bit(self.params, f"{self.name}_INV", i)
        return enabled & inputs.get(f"INP{i + 1}", False) ^ inverted

    def _get_next_outputs(self, inputs: Inputs) -> Outputs:
        op = and_ if self.name.startswith("AND") else or_
        get_input = partial(self._get_input, inputs)
        outputs = self.Outputs(OUT=reduce(op, map(get_input, range(4))))
        self.last_input = inputs
        return outputs


@pydantic.v1.dataclasses.dataclass
class AndOrBlockConfig(BlockConfig):
    def __call__(self) -> DeviceComponent:
        return DeviceComponent(name=self.name, device=AndOrBlock(name=self.name))
