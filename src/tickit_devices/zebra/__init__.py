from typing import List

import pydantic.v1.dataclasses
from pydantic import Field
from tickit.adapters.io import TcpIo
from tickit.core.adapter import AdapterContainer
from tickit.core.components.system_simulation import (
    SystemSimulation,
    SystemSimulationComponent,
)
from tickit.core.typedefs import ComponentID

from tickit_devices.zebra._common import default_filler, mux_types, param_types
from tickit_devices.zebra.and_or_block import AndOrBlockConfig, BlockConfig
from tickit_devices.zebra.zebra import ZebraAdapter


@pydantic.v1.dataclasses.dataclass
class Zebra(SystemSimulation):
    """Zebra simulation with TCP server."""

    host: str = "localhost"
    port: int = 7012
    params: dict[str, int] = Field(default_factory=default_filler(param_types))
    muxes: dict[str, int] = Field(default_factory=default_filler(mux_types))
    components = List[BlockConfig]

    def __call__(self) -> SystemSimulationComponent:
        andor_blocks = [
            AndOrBlockConfig(name=ComponentID(f"{ANDOR}{num}"), params=self.params)
            for ANDOR in {"AND", "OR"}
            for num in range(4)
        ]
        return SystemSimulationComponent(
            adapter=AdapterContainer(
                adapter=ZebraAdapter(params=self.params, muxes=self.muxes),
                io=TcpIo(host=self.host, port=self.port),
            ),
            components=andor_blocks,
            expose=self.expose,
            name=self.name,
        )
