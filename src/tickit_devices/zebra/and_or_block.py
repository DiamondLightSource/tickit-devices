from abc import ABC
from dataclasses import dataclass
from functools import partial, reduce
from operator import and_, or_
from typing import Dict

from tickit.core.components.component import ComponentConfig
from tickit.core.device import DeviceUpdate
from tickit.core.typedefs import SimTime, Changes, ComponentID
from typing_extensions import TypedDict

from ._common import Block, extract_bit


class Inputs(TypedDict):
    INP1: bool
    INP2: bool
    INP3: bool
    INP4: bool


class Outputs(TypedDict):
    OUT: bool


class AndOrBlock(Block):
    """Represents an AND or OR gate"""

    async def stop_component(self) -> None:
        pass

    def _get_input(self, inputs: Dict[str, bool], i: int) -> bool:
        enabled = extract_bit(self.params, f"{self.name}_ENA", i)
        inverted = extract_bit(self.params, f"{self.name}_INV", i)
        return enabled & inputs[f"INP{i+1}"] ^ inverted

    def on_tick(self, time: SimTime, changes: Changes) -> DeviceUpdate[Outputs]:
        op = and_ if self.name.startswith("AND") else or_
        get_input = partial(self._get_input, changes)
        outputs = Outputs(OUT=reduce(op, map(get_input, range(4))))
        return DeviceUpdate(outputs, call_at=None)


@dataclass
class BlockConfig(ComponentConfig, ABC):
    params: dict[str, int]

    def __init__(self, name: ComponentID,
                 params: dict[str, int]):
        super().__init__(name, inputs={})
        self.params = params


@dataclass
class AndOrBlockConfig(BlockConfig):

    def __init__(self, name: ComponentID,
                 params: dict[str, int]):
        super().__init__(name, params)

    def __call__(self) -> AndOrBlock:
        return AndOrBlock(self.name, self.params)
