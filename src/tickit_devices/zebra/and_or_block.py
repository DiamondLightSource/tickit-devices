from abc import ABC, abstractmethod
from functools import partial, reduce
from operator import and_, or_
from typing import Dict, TypedDict

import pydantic.v1.dataclasses
from tickit.core.components.component import ComponentConfig
from tickit.core.device import DeviceUpdate
from tickit.core.typedefs import Changes, SimTime

from tickit_devices.zebra._common import Block, extract_bit


class AndOrBlock(Block):
    """Represents an AND or OR gate"""

    class Inputs(TypedDict):
        INP1: bool
        INP2: bool
        INP3: bool
        INP4: bool

    class Outputs(TypedDict):
        OUT: bool

    async def stop_component(self) -> None:
        pass

    def _get_input(self, inputs: Dict[str, bool], i: int) -> bool:
        enabled = extract_bit(self.params, f"{self.name}_ENA", i)
        inverted = extract_bit(self.params, f"{self.name}_INV", i)
        return enabled & inputs[f"INP{i + 1}"] ^ inverted

    def on_tick(self, time: SimTime, changes: Changes) -> DeviceUpdate[Outputs]:
        op = and_ if self.name.startswith("AND") else or_
        get_input = partial(self._get_input, changes)
        outputs = self.Outputs(OUT=reduce(op, map(get_input, range(4))))
        return DeviceUpdate(outputs, call_at=None)  # type: ignore


@pydantic.v1.dataclasses.dataclass
class BlockConfig(ComponentConfig, ABC):

    @abstractmethod
    def __call__(self, params: Dict[str, int] = None) -> Block:
        """Create the component from the given config with the shared params"""
        ...


class AndOrBlockConfig(BlockConfig):

    def __call__(self, params: Dict[str, int] = None) -> Block:
        """Create the component from the given config with the shared params"""
        if params is None:
            raise TypeError
        return AndOrBlock(name=self.name, params=params)
