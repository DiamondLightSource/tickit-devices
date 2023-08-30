from functools import partial, reduce
from operator import and_, or_
from typing import Dict, TypedDict

import pydantic.v1.dataclasses
from tickit.core.components.device_simulation import DeviceSimulation
from tickit.core.device import DeviceUpdate
from tickit.core.typedefs import SimTime

from tickit_devices.zebra._common import Block, BlockConfig, extract_bit


class AndOrBlock(Block):
    """
    Represents an AND or OR gate with 4 inputs.
    If an input is not enabled, it will always be considered False,
    unless it is also inverted.
    """

    last_input: "AndOrBlock.Inputs"

    class Inputs(TypedDict):
        INP1: bool
        INP2: bool
        INP3: bool
        INP4: bool

    class Outputs(TypedDict):
        OUT: bool

    def _get_input(self, inputs: Dict[str, bool], i: int) -> bool:
        if not self.params:
            raise ValueError
        enabled = extract_bit(self.params, f"{self.name}_ENA", i)
        inverted = extract_bit(self.params, f"{self.name}_INV", i)
        return enabled & inputs.get(f"INP{i + 1}", False) ^ inverted

    def read_mux(self, inp: str) -> int:
        # TODO: Is there a better way of getting the input from the adapter?
        return int(self.last_input[inp] if self.last_input else False)  # type: ignore

    def set_mux(self, register: str, value: int) -> int:
        # TODO: Does this do everything it needs to?
        self.update(
            SimTime(0),
            AndOrBlock.Inputs(
                **self.last_input
                or {
                    "INP1": False,
                    "INP2": False,
                    "INP3": False,
                    "INP4": False,
                },
                **{register: bool(value)},
            ),
        )
        return value

    def update(self, time: SimTime, inputs: Inputs) -> DeviceUpdate[Outputs]:
        op = and_ if self.name.startswith("AND") else or_
        get_input = partial(self._get_input, inputs)
        outputs = self.Outputs(OUT=reduce(op, map(get_input, range(4))))
        self.last_input = inputs
        return DeviceUpdate(outputs, call_at=None)  # type: ignore


@pydantic.v1.dataclasses.dataclass
class AndOrBlockConfig(BlockConfig):
    def __call__(self) -> DeviceSimulation:
        return DeviceSimulation(name=self.name, device=AndOrBlock(name=self.name))
