from typing import Dict, List

import pydantic.v1.dataclasses
from pydantic import Field
from tickit.adapters.io import TcpIo
from tickit.core.adapter import AdapterContainer
from tickit.core.components.component import ComponentConfig
from tickit.core.components.system_simulation import (
    SystemSimulationComponent,
)
from tickit.core.typedefs import ComponentID, PortID, ComponentPort

from tickit_devices.zebra._common import default_filler, mux_types, param_types
from tickit_devices.zebra.and_or_block import AndOrBlockConfig, BlockConfig
from tickit_devices.zebra.zebra import ZebraAdapter


@pydantic.v1.dataclasses.dataclass
class Zebra(ComponentConfig):
    """Zebra simulation with TCP server."""

    name: ComponentID
    inputs: Dict[PortID, ComponentPort]
    components: List[BlockConfig]
    expose: Dict[PortID, ComponentPort]
    host: str = "localhost"
    port: int = 7012
    params: dict[str, int] = Field(default_factory=default_filler(param_types))
    muxes: dict[str, int] = Field(default_factory=default_filler(mux_types))

    def __call__(self) -> SystemSimulationComponent:
        return SystemSimulationComponent(
            adapter=AdapterContainer(
                adapter=ZebraAdapter(params=self.params, muxes=self.muxes),
                io=TcpIo(host=self.host, port=self.port),
            ),
            components=self.components,
            expose=self.expose,
            name=self.name,
        )
